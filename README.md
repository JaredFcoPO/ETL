# Comparador de Queries Presupuestales (ETL)

Un pipeline ETL modular construido en Python diseñado para extraer, validar y comparar dinámicamente la salida de consultas SQL presupuestales (Original vs. Actualizada). El sistema genera un reporte automatizado en Excel con formato financiero, detallando las diferencias en dimensiones, valores nulos, cifras de calendario y datos descriptivos.

## Características Principales

* **Generación Dinámica de Llaves:** Crea llaves compuestas únicas en tiempo de ejecución para cruzar grandes volúmenes de datos de forma precisa.
* **Validación Estructural:** Identifica columnas faltantes o añadidas entre las dos versiones de las consultas.
* **Auditoría de Vacíos (Nulos):** Mapea y cuantifica las cadenas vacías (`''`) introducidas durante la limpieza de datos.
* **Cruce de Calendario y Descriptivos:** Compara importes numéricos mes a mes e identifica cambios en campos descriptivos (claves presupuestarias, ramos, etc.).
* **Exportación "Modo Pro":** Consolida todos los hallazgos en un único archivo de Excel (`.xlsx`) con múltiples pestañas, anchos automáticos y formato de moneda contable utilizando `xlsxwriter`.

## Estructura del Proyecto

El proyecto sigue una arquitectura modular y segura para ambientes de producción:

```text
Comparativo_queries/
│
├── data/
│   └── output/             # Directorio destino de los reportes generados
├── notebooks/              # Análisis exploratorio y pruebas en Jupyter
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

```Bash
git clone [https://github.com/JaredFcoPO/Comparativo_queries.git](https://github.com/JaredFcoPO/Comparativo_queries.git)
cd Comparativo_queries
```