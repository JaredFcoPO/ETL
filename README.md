# Comparador de Queries Presupuestales (ETL)

Un pipeline ETL modular construido en Python diseñado para extraer, validar y comparar dinámicamente la salida de consultas SQL presupuestales
(Original vs. Actualizada). El sistema genera un reporte automatizado en Excel con formato financiero, detallando las diferencias en dimensiones, valores nulos,
cifras de calendario y datos descriptivos.

## Características Principales

* **Generación Dinámica de Llaves:** Crea llaves compuestas únicas en tiempo de ejecución para cruzar grandes volúmenes de datos de forma precisa.
* **Validación Estructural:** Identifica columnas faltantes o añadidas entre las dos versiones de las consultas.
* **Auditoría de Vacíos (Nulos):** Mapea y cuantifica las cadenas vacías (`''`) introducidas durante la limpieza de datos.
* **Cruce de Calendario y Descriptivos:** Compara importes numéricos mes a mes e identifica cambios en campos descriptivos (claves presupuestarias, ramos, etc.).
* **Exportación "Modo Pro":** Consolida todos los hallazgos en un único archivo de Excel (`.xlsx`) con múltiples pestañas, anchos automáticos y formato de
moneda contable utilizando `xlsxwriter`.

## Estructura del Proyecto

El proyecto sigue una arquitectura modular y segura para ambientes de producción:

```text
Comparativo_queries/
│
├── data/
│   └── output/             # Directorio destino de los reportes generados
├── queries/                # Archivos .txt o .sql con las consultas originales y actualizadas
├── src/                    # Módulos de procesamiento lógico
│   ├── base_datos.py       # Conexión al motor de base de datos mediante SQLAlchemy
│   ├── config.py           # Gestor de variables de entorno y configuración
│   └── ETL.py              # Funciones core de extracción, transformación y exportación
│
├── .env                    # Credenciales de conexión (Excluido en .gitignore)
├── config.json             # Archivo de configuración para columnas dinámicas
├── main.py                 # Orquestador principal del pipeline
└── README.md               # Documentación del proyecto
```

## Configuración Inical
1. Clonar el repositorio
```Bash
git clone [https://github.com/JaredFcoPO/Comparativo_queries.git](https://github.com/JaredFcoPO/Comparativo_queries.git)
cd Comparativo_queries
```
2. Instalar dependencias

````Bash
pip install pandas sqlalchemy psycopg2 python-dotenv xlsxwriter
````
3. Configurar el entorno seguro (.env)
Crea un archivo .env en la raíz del proyecto con las siguientes credenciales para tu conexión a Postgresql (El archivo es ignorado por git por seguridad)

* usuario=TU_USUARIO 
* password=TU_PASSWORD 
* host=TU_HOST 
* database=TU_BASE_DE_DATOS 
* port=5432

4. Definir esquemas dinámicos (config.json):
Asegúrate que el archivo config.json contenga las listas actualizadas de tus columnas de importe y columnas descriptivas.
````JSON
{
  "columnas_importes": ["enero", "febrero", "marzo", ...],
  "columnas_descriptivos": ["clave_presupuestaria", "anio", "ramo", ...]
}
````

## Uso
Para ejecutar el pipeline corre el orquestador principal desde la raíz del proyecto:
````Bash
python main.py
````
El script interactivo te solicitará:
1. La ruta del archivo .sql de tu query original
2. La ruta del archivo .sql de tu query actualizada
3. Los nombres de las columnas que formarán la llave primaria, separadas por comas (ejemplo, operacion, clave).
