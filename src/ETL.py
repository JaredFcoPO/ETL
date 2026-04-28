
from sqlalchemy import text
import pandas as pd
from src.base_datos import *
import os

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
    diferencias.rename(columns={'self':'Archivo_Original','other':'Archivo_Actualizado'}, level=1,inplace=True)
    diferencias.columns = ['_'.join(col) for col in diferencias.columns]
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


def registros_nulos(df_original, df_actualizada):
    nulos_original = (df_original == '').sum()
    nulos_original = nulos_original.reset_index()
    nulos_original.columns = ['Columna', 'Total_Nulos']
    nulos_actualizada = (df_actualizada == '').sum()
    nulos_actualizada = nulos_actualizada.reset_index()
    nulos_actualizada.columns = ['Columna', 'Total_Nulos']
    columnas_vacias_original = nulos_original[nulos_original.Total_Nulos>0]
    columnas_vacias_actualizada = nulos_actualizada[nulos_actualizada.Total_Nulos>0]
    return  columnas_vacias_original, columnas_vacias_actualizada


def genera_reporte(diccionarios_dfs, archivo = 'reporte_completo.xlsx'):
    os.makedirs(os.path.dirname(archivo), exist_ok=True)
    print(f"Generando reporte en: {archivo}...")
    if diccionarios_dfs:
        with pd.ExcelWriter(archivo, engine='xlsxwriter') as writer:
            for hoja, df in diccionarios_dfs.items():
                if df is not None and not df.empty:
                    repo_con_llave = ['Cruce Completo', 'Valida_descriptivos']
                    usar_indice = True if hoja in repo_con_llave else False
                    df.to_excel(writer, sheet_name=hoja, index=usar_indice)
                    workbook = writer.book
                    worksheet = writer.sheets[hoja]
                    formato_moneda = workbook.add_format({'num_format':'#,##0.00'})
                    worksheet.set_column('A:A', 15)
                    worksheet.set_column('B:AZ', 15)
                    if hoja == 'Valida_calendario':
                        worksheet.set_column('B:E', 17, formato_moneda)
        print("Reporte generado con éxito")
    else:
        print("El diccionario de resultado está vacío, no hay nada que exportar")


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
    dif.rename(columns={'self':'Archivo_Original','other':'Archivo_Actualizada'}, level = 1, inplace=True)
    dif.columns = ['_'.join(col) for col in dif.columns]
    return dif

