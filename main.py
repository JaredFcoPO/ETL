# Probando...

from ETL import *
if __name__ == '__main__':
    ruta_original = recibe_ruta("Dame la ruta de tu query original: ")
    ruta_actualizada = recibe_ruta("Dame la ruta de tu query actualizada: ")
    llave = recibe_llave("Dame las columnas que formaran la llave de las queries: ")
    query_original_txt = cargar_query(ruta_original)
    query_actualizada_txt = cargar_query(ruta_actualizada)
    df_original = extraer_datos(query_original_txt, engine)
    df_actualizada = extraer_datos(query_actualizada_txt, engine)
    calendario = valida_calendario(df_original, df_actualizada)
    claves_desc = valida_descriptivos(df_original, df_actualizada)
    tabla_dimensiones, columnas_originales, columnas_actualizadas = get_dimensiones(df_original, df_actualizada)
    comunes, solo_original, solo_actualizado, dif_total = valida_dimensiones(columnas_originales, columnas_actualizadas)
    columnas_comunes = list(comunes)
    a, b = armar_llave_df(df_original, df_actualizada, llave)
    final = compara_todo(a, b, columnas_comunes)
    exporta_df(calendario)
    exporta_df(claves_desc)
    exporta_df(tabla_dimensiones)
    exporta_df(final)
    print(f'El número de columnas en común: {len(columnas_comunes)}')
    print(f'Nombre de las columnas que sólo están en la query original:{','.join(solo_original)}')
    print(f'Nombre de las columnas que sólo están en la query actualizado:{','.join(solo_actualizado)}')
    print(f'Las diferencias totales son: {','.join(dif_total)}')
    print('Datos extraídos al df')

