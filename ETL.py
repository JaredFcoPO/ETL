from base_datos import *
from sqlalchemy import text
import pandas as pd

columnas_importes = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre',
                         'octubre', 'noviembre', 'diciembre', 'anual']
columnas_descriptivos = ['clave_presupuestaria','anio','ramo','institucion','unidad_responsable','finalidad','funcion','subfuncion','programa_presupuestario','subprograma_presupuestario','actividad_institucional','identificador_gasto','fuente_financiamiento','origen','procedencia','actividad_especifica','partida_especifica','tipo_gasto','region','municipio','ppi']

def recibe_ruta(mensaje):
    mensaje = input(mensaje)
    ruta = mensaje.replace("\\", "/")
    return ruta

def cargar_query(ruta):
    with open(ruta, 'r', encoding='utf8') as f:
        return f.read()

def extraer_datos(texto_query, engine):
    df = pd.read_sql(text(texto_query), engine)
    df = df.replace(r'^\s*$','', regex=True)
    df = df.fillna('')
    for column in columnas_importes:
        df[column] = pd.to_numeric(df[column], errors='coerce')
    return df

def valida_calendario(df_original, df_actualizada):
    pd.set_option('display.float_format', '{:,.2f}'.format)
    calendarios_original = df_original[columnas_importes].sum()
    calendarios_actualizada = df_actualizada[columnas_importes].sum()
    df_original_c = calendarios_original.reset_index()
    df_actualizada_c = calendarios_actualizada.reset_index()
    df_original_c.columns = ['Mes', 'Total_Original']
    df_actualizada_c.columns = ['Mes', 'Total_Actualizado']
    df_valida_calendarios = pd.merge(df_original_c, df_actualizada_c, on='Mes', how='inner')
    df_valida_calendarios['Diferencia'] = df_valida_calendarios['Total_Original'] - df_valida_calendarios[
        'Total_Actualizado']
    return df_valida_calendarios

def valida_descriptivos(df_original, df_actualizada):
    df_original_descriptivos = df_original[columnas_descriptivos]
    df_actualizada_descriptivos = df_actualizada[columnas_descriptivos]
    df_original_descriptivos_index = df_original_descriptivos.set_index('clave_presupuestaria').sort_index()
    df_actualizada_descriptivos_index = df_actualizada_descriptivos.set_index('clave_presupuestaria').sort_index()
    df_original_descriptivos_index = df_original_descriptivos_index.reindex(
        sorted(df_original_descriptivos_index.columns), axis=1)
    df_actualizada_descriptivos_index = df_actualizada_descriptivos_index.reindex(
        sorted(df_actualizada_descriptivos_index.columns), axis=1)
    diferencias = df_original_descriptivos_index.compare(df_actualizada_descriptivos_index, align_axis=1)
    return diferencias

def get_dimensiones(df_original, df_actualizada):
    columnas_original = df_original.columns
    columnas_actualizada = df_actualizada.columns
    dimensiones_original = df_original.shape
    dimensiones_actualizada = df_actualizada.shape
    dimensiones = [dimensiones_original + ('Original',), dimensiones_actualizada + ('Actualizada',)]
    df_dimensiones = pd.DataFrame(dimensiones, columns=['Registros', 'Columnas', 'Origen'])
    return df_dimensiones, columnas_original, columnas_actualizada

def valida_dimensiones(col_ori, col_act):
    a = set(col_ori)
    b = set(col_act)
    ambos = a & b
    solo_a = a - b
    solo_b = b - a
    diferencias = a ^ b
    return ambos, solo_a, solo_b, diferencias

## Por la conversión de nulos a vacíos esto ya no sirve, tendríamos que buscar ahora lo que sea ''
def registros_nulos(df_original, df_actualizada):
    nulos_original = df_original.isnull().sum()
    nulos_original = nulos_original.reset_index()
    nulos_original.columns = ['Columna', 'Total_Nulos']
    nulos_actualizada = df_actualizada.isnull().sum()
    nulos_actualizada = nulos_actualizada.reset_index()
    nulos_actualizada.columns = ['Columna', 'Total_Nulos']

def exporta_df(data):
    if not data.empty:
        data.to_excel('diferencias.xlsx')
        print('Reporte_generado')
    else:
        print('No hay diferencias')

def recibe_llave(mensaje):
    texto = input(mensaje)
    lista_cruda = texto.replace(" ","").split(",")
    # Candado: List comprehension para evitar elementos vacíos como '',['a', 'b', 'cc', '']
    # Guarda el elemento 'x' por cada 'x' en la lista, solamente si 'x' no está vacío
    llave_limpia = [x for x in lista_cruda if x]
    return llave_limpia

def armar_llave_df(df_original, df_actualizada, llave_limpia):
    df_original['LLAVE'] = df_original[llave_limpia].astype(str).agg('-'.join, axis=1)
    df_actualizada['LLAVE'] = df_actualizada[llave_limpia].astype(str).agg('-'.join, axis=1)
    return df_original, df_actualizada


def compara_todo(df_original, df_actualizada, columnas_comunes):
    df_original_index = df_original[columnas_comunes].copy()
    df_actualizada_index = df_actualizada[columnas_comunes].copy()
    df_original_index = df_original_index.set_index('LLAVE').sort_index()
    df_actualizada_index = df_actualizada_index.set_index('LLAVE').sort_index()
    df_original_index = df_original_index.reindex(sorted(df_original_index.columns), axis=1)
    df_actualizada_index = df_actualizada_index.reindex(sorted(df_actualizada_index.columns), axis=1)
    dif = df_original_index.compare(df_actualizada_index, align_axis=1)
    return dif

