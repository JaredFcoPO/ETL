from dotenv import load_dotenv
import os
import json

# 1. Obtenemos la ruta absoluta de donde está este archivo (src/config.py)
ruta_de_este_script = os.path.dirname(os.path.abspath(__file__))

# 2. Construimos la ruta al JSON subiendo un nivel (..) a la raíz
# Esto une: Carpeta_Proyecto/src + .. + colums.json
ruta_json = os.path.join(ruta_de_este_script, "..", "colums.json")

load_dotenv()
usuario = os.getenv("usuario")
contrasena = os.getenv("password")
host = os.getenv("host")
database = os.getenv("database")
port = os.getenv("port")
with open(ruta_json, 'r', encoding='utf-8') as f:
    config = json.load(f)
columnas_importes = config["columnas_importes"]
columnas_descriptivos = config["columnas_descriptivos"]
ruta_output = config["ruta_output"]