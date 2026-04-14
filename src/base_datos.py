from sqlalchemy import create_engine
from src.config import *

cadena_c = f'postgresql://{usuario}:{contrasena}@{host}:{port}/{database}'
engine = create_engine(cadena_c)