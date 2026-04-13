from dotenv import load_dotenv
import os

load_dotenv()
usuario = os.getenv("usuario")
contrasena = os.getenv("password")
host = os.getenv("host")
database = os.getenv("database")
port = os.getenv("port")

