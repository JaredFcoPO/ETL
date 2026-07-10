import pandas as pd
from sqlalchemy import create_engine, text
import xlsxwriter
from xlsxwriter import workbook, worksheet
from datetime import datetime
import time
import os



def obtener_dimensiones_df(df):
    """
    Obtiene de un dataframe el número de filas/columnas y la lista de nombres de las columnas
    :param df: Recibe un dataframe
    :return: Regresa un dataframe con las dimensiones y las columnas del dataframe original
    """
    columnas_df = df.columns
    dimensiones_df = df.shape
    df_dimensiones = [dimensiones_df]
    df_dimensiones = pd.DataFrame(df_dimensiones, columns=['Registros', 'Columnas'])
    return df_dimensiones, columnas_df

def valida_dimensiones(col_df_1, col_df_2):
    """
    Comparación de dos listas de columnas usando teoría de conjuntos
    :param col_df_1: Columna del dataframe original
    :param col_df_2: Columna del dataframe actualizado
    :return: Regresa las operaciones de conjuntos realizadas
    """
    a = set(col_df_1)
    b = set(col_df_2)
    ambos = a & b
    solo_a = a - b
    solo_b = b - a
    diferencias = a ^ b
    return diferencias, solo_a, solo_b, ambos


class LectorDatos:
    def __init__(self, usuario, contrasena, host, port, database):
        self.usuario = usuario
        self.contrasena = contrasena
        self.host = host
        self.port = port
        self.database = database
        self.cadena_conexion = f'postgresql://{usuario}:{contrasena}@{host}:{port}/{database}'
        self.engine = None

    def genera_dataframe(self, ruta):
        """
        Orquesta la generación de un dataframe a partir de la ruta.
        :param ruta: Recibe la ruta del archivo
        :return: Regresa un dataframe a partir de la ruta y del tipo de archivo
        """
        if not ruta:
            print('La ruta no es válida')
            return None
        if ruta.endswith('.xlsx'):
            df = self._leer_excel(ruta)
        elif ruta.endswith('.txt') or ruta.endswith('.sql'):
            texto_query = self._leer_archivo_texto(ruta)
            df = self._ejecutar_query(texto_query)
        else:
            print(f'Formato no soportado para el archivo: {ruta}, favor de verificar.')
            return None
        return df
    @staticmethod
    def _leer_excel(ruta):
        return pd.read_excel(ruta)
    @staticmethod
    def _leer_archivo_texto(ruta):
        with open(ruta, 'r', encoding='utf-8') as f:
            return f.read()
    def _ejecutar_query(self, texto_query):
        if self.engine is None:
            self.engine = create_engine(self.cadena_conexion)
        return pd.read_sql(text(texto_query), con=self.engine)

class ConciliadorETL:
    def __init__(self, columnas_importes, columnas_descriptivos, llave, col_concepto, clave_p):
        self.columnas_importes = columnas_importes
        self.columnas_descriptivos = columnas_descriptivos
        self.llave = llave
        self.col_concepto = col_concepto
        self.clave_p = clave_p


    def limpia_dataframe(self, df):
        """
        Limpia los nulos y los convierte a cadenas vacías y redondea los número a dos decimales
        :param df: Recibe el dataframe para limpiar
        :return:
        """
        df = df.replace(r'^\s*$', '', regex=True)
        df = df.fillna('')
        for column in self.columnas_importes:
            df[column] = pd.to_numeric(df[column], errors='coerce').round(2).fillna(0)
        return df

    def valida_importes_concepto(self, df_1, df_2):
        """
        Compara los totales a nivel de concepto de las columnas importes
        :param df_1: Recibe un dataframe origen
        :param df_2: Recibe un dataframe actualizado
        :return: Regresa un dataframe con el comparativo entre los anteriores.
        """
        importes_1 = df_1[self.columnas_importes].sum().reset_index()
        importes_2 = df_2[self.columnas_importes].sum().reset_index()
        importes_1.columns = self.col_concepto
        importes_2.columns = self.col_concepto
        columna_union = self.col_concepto[0]
        columna_importes = self.col_concepto[1]
        comparativo = pd.merge(importes_1, importes_2, on=columna_union, how='inner', suffixes=('_1', '_2'))
        col_1 = f'{columna_importes}_1'
        col_2 = f'{columna_importes}_2'
        comparativo['Diferencia'] = (comparativo[col_2] - comparativo[col_1]).round(2)
        return comparativo

    def valida_importes_claves(self, df_1, df_2):
        """
        Compara los totales a nivel de clave de las columnas importes
        :param df_1: Recibe un dataframe origen
        :param df_2: Recibe un dataframe actualizado
        :return: Regresa cinco dataframe con los resultados del comparativo,
        """
        validacion = pd.merge(df_1, df_2, on=self.llave, how='outer', suffixes=('_1', '_2'), indicator=True)
        columnas_diff = []
        nulos_faltan_en_df_2 = validacion[validacion['_merge'] == 'left_only'].copy()
        nulos_faltan_en_df_1 = validacion[validacion['_merge'] == 'right_only'].copy()
        nulos = validacion[validacion['_merge'] != 'both'].copy()

        for col in self.columnas_importes:
            col_1 = f'{col}_1'
            col_2 = f'{col}_2'
            col_dif = f'{col}_dif'
            validacion[col_dif] = (validacion[col_2].fillna(0) - validacion[col_1].fillna(0)).round(2)
            columnas_diff.append(col_dif)
        solo_cambios = validacion[(validacion[columnas_diff] != 0).any(axis=1)].copy()
        for df_temp in [validacion, solo_cambios, nulos,nulos_faltan_en_df_1, nulos_faltan_en_df_2]:
            if '_merge' in df_temp.columns:
                df_temp.drop(columns=['_merge'], inplace=True)
        return validacion, solo_cambios, nulos, nulos_faltan_en_df_1, nulos_faltan_en_df_2

    def valida_descriptivos(self, df_1, df_2):
        llave_lista = self.clave_p if isinstance(self.clave_p, list) else [self.clave_p]
        columnas_a_filtrar = list(set(self.columnas_descriptivos + llave_lista))
        df_1_descriptivos = df_1[columnas_a_filtrar].copy()
        df_2_descriptivos = df_2[columnas_a_filtrar].copy()
        df_1_descriptivos_index = df_1_descriptivos.set_index(self.clave_p).sort_index()
        df_2_descriptivos_index = df_2_descriptivos.set_index(self.clave_p).sort_index()
        df_1_descriptivos_index = df_1_descriptivos_index.reindex(sorted(df_1_descriptivos_index.columns), axis=1)
        df_2_descriptivos_index = df_2_descriptivos_index.reindex(sorted(df_2_descriptivos_index.columns), axis=1)
        llaves_comun = df_1_descriptivos_index.index.intersection(df_2_descriptivos_index.index)
        df_1_comun = df_1_descriptivos_index.loc[llaves_comun]
        df_2_comun = df_2_descriptivos_index.loc[llaves_comun]
        diferencias = df_1_comun.compare(df_2_comun, align_axis = 1)
        if not diferencias.empty:
            diferencias.rename(columns={'self':'archivo_1', 'other':'archivo_2'}, inplace=True, level=1)
            diferencias.columns = ['_'.join(col) for col in diferencias.columns]
        return diferencias

    @staticmethod
    def exporta_resultados(diccionario_resultados, limite = 50000):
        timestamp = datetime.now().strftime("%d-%m-%Y %H-%M-%S")
        nombre_archivo = f'resultado_{timestamp}.xlsx'
        resultados_excel = {}
        for hoja, df in diccionario_resultados.items():
            if df is not None and not df.empty:
                if df.shape[0] > limite:
                    nombre_csv = f'{hoja}_{timestamp}.csv'
                    usar_indice = True if df.index.name else False
                    df.to_csv(nombre_csv, index=usar_indice, encoding='utf-8-sig')
                    df_aviso = pd.DataFrame({
                        'estatus': ['Exportado a csv por volumne'],
                        'total_registros':[df.shape[0]],
                        'nombre_archivo':[nombre_csv],
                        'nota':['Abrir el archivo csv para mayor detalle']
                    })
                    resultados_excel[hoja] = df_aviso
            else:
                resultados_excel[hoja] = df
        if diccionario_resultados:
            with pd.ExcelWriter(nombre_archivo, engine='xlsxwriter') as writer:
                for hoja, df in diccionario_resultados.items():
                    if df is not None and not df.empty:
                        usar_indice = True if df.index.name else False
                        df.to_excel(writer, sheet_name=hoja, index=usar_indice, header=True)
                        workbook = writer.book
                        worksheet = writer.sheets[hoja]
                        formato_numero = workbook.add_format({'num_format': '#,##0.00;[Red]-#,##0.00'})
                        formato_aviso = workbook.add_format({'bold':True})
                        offset = 1 if usar_indice else 0
                        if 'estatus' in df.columns:
                            worksheet.set_column(0, 0, 30, formato_aviso)
                            worksheet.set_column(1, 1, 15)
                            worksheet.set_column(2, 2, 40)
                            worksheet.set_column(3, 3, 60)
                            continue
                        for col_idx, col_name in enumerate(df.columns):
                            if pd.api.types.is_numeric_dtype(df[col_name]):
                                worksheet.set_column(col_idx + offset,col_idx + offset, 18,formato_numero)
                            else:
                                worksheet.set_column(col_idx + offset,col_idx + offset,25)
            print(f"Reporte generado: {nombre_archivo}")
        else:
            print("No hay resultados que exportar")


if __name__ == '__main__':
    inicio_total = time.time()
    print(f"[{datetime.now().strftime('%d-%m-%Y %H-%M-%S')}] 1. Iniciando proceso ETL")
    lector = LectorDatos('postgres','123','172.28.14.94','65535','siafdb')
    # df_origen = lector.genera_dataframe("C:/Users/JFPO/Documents/Prueba_Acumulado_03.06.2026.xlsx")
    # df_actualizada = lector.genera_dataframe("C:/Users/JFPO/Documents/Prueba_Acumulado_04.06.2026.xlsx")
    inicio_paso = time.time()
    print(f"[{datetime.now().strftime('%d-%m-%Y %H-%M-%S')}] 2. Extrayendo datos de origen...")
    df_origen = lector.genera_dataframe("C:/Users/JFPO/PycharmProjects/Comparativo_queries/Sábanas/queries/Originales/CLC_Original.sql")
    df_actualizada = lector.genera_dataframe("C:/Users/JFPO/PycharmProjects/Comparativo_queries/Sábanas/queries/Actualizados/CLC_Actualizado_claves.sql")

    # Obtenemos las columnas del dataframe
    _, columnas_1 = obtener_dimensiones_df(df_origen)
    _, columnas_2 = obtener_dimensiones_df(df_actualizada)
    # Usamos las columnas que están en ambos dataframes
    _,solo_a,solo_b, columnas_comun = valida_dimensiones(columnas_1, columnas_2)
    print(f"Extracción terminada en {time.time() - inicio_paso:.2f} segundos.")
    print(f"Filas Origen: {df_origen.shape[0]}| Filas Actualizada: {df_actualizada.shape[0]}")
    # Reglas
    columnas_importes = ['enero','febrero','marzo','abril',
                         'mayo','junio','julio','agosto',
                         'septiembre','octubre','noviembre','diciembre']
    llave = ['folio','clave_presupuestaria'] ##todo: en un input
    col_concepto = ['Calendario', 'Total'] ## todo: en un input
    columnas_descriptivos = ["clave_presupuestaria","anio","ramo","institucion","unidad_responsable",
    "finalidad","funcion","subfuncion","programa_presupuestario",
    "subprograma_presupuestario","actividad_institucional","identificador_gasto",
    "fuente_financiamiento","origen","procedencia","actividad_especifica",
    "partida_especifica","tipo_gasto","region","municipio","ppi"]
    conciliador = ConciliadorETL(columnas_importes, columnas_descriptivos, llave, col_concepto)

    if df_origen is not None and df_actualizada is not None:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 3. Limpiando DataFrame... ")
        inicio_paso = time.time()
        df_origen = conciliador.limpia_dataframe(df_origen)
        df_actualizada = conciliador.limpia_dataframe(df_actualizada)
        print(f" Limpieza terminada en {time.time() - inicio_paso:.2f} segundos.")

        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 4. Ejecutando validaciones de importes a nivel de concepto... ")
        inicio_paso = time.time()
        comparativo_totales = conciliador.valida_importes_concepto(df_origen, df_actualizada)
        print(f"Validaciones matemáticas terminadas en {time.time() - inicio_paso:.2f} segundos.")

        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 5. Ejecutando validaciones a nivel de llave")
        inicio_paso = time.time()
        comparativo_llave, solo_cambios, registros_nulos, nulo_falta_1, nulo_falta_2  = conciliador.valida_importes_claves(df_origen, df_actualizada)
        print(f"Validaciones terminadas en {time.time() - inicio_paso:.2f} segundos.")
        print(f"Resultados preliminares: {len(solo_cambios)} con diferencias | {len(nulo_falta_1)} nuevos | {len(nulo_falta_2)} faltantes")

        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 6. Ejecutando validaciones de descriptivos")
        inicio_paso = time.time()
        diferencias_desc = conciliador.valida_descriptivos(df_origen, df_actualizada)

        print(f"Validaciones terminadas en {time.time() - inicio_paso:.2f} segundos.")

        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 7. Exportando resultados")
        inicio_paso = time.time()
        df_estructura = pd.DataFrame(
            {'Solo_origen':list(solo_a) if solo_a else [None],
             'Solo_actualizada':list(solo_b) if solo_b else [None],
             'Columnas_comun': list(columnas_comun) if columnas_comun else [None]
             })
        diccionario_exportacion = {
            'Claves_cambios': solo_cambios,
            'Nulos_primer_df': nulo_falta_1,
            'Nulos_segundo_df': nulo_falta_2
        }
        print("Exportando resultados...")
        conciliador.exporta_resultados(diccionario_exportacion, limite=50000)
        print(f"Resultados exportados en {time.time() - inicio_paso:.2f} segundos.")
        tiempo_total = (time.time() - inicio_total)/60
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Proceso completado en {tiempo_total:.2f} minutos")
    else:
        print("No hay resultados que exportar")