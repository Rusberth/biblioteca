"""Configuración de la aplicación Biblioteca (Flask AppBuilder + MySQL).

Los valores sensibles (clave secreta, usuario y contraseña de la base de datos)
se leen del archivo .env para no subirlos al repositorio. Si no existe .env se
usan los valores por defecto de XAMPP: usuario root, sin contraseña, puerto 3306.
"""
import os
from urllib.parse import quote_plus

from dotenv import load_dotenv
from flask_appbuilder.const import AUTH_DB

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, ".env"))

# --------------------------------------------------------------------------
# Seguridad
# --------------------------------------------------------------------------
# Clave secreta de la aplicación (mínimo 20 caracteres).
SECRET_KEY = os.getenv("SECRET_KEY", "cambia-esta-clave-por-una-larga-y-aleatoria")

# Protección CSRF para los formularios de Flask-WTF
CSRF_ENABLED = True

# Autenticación contra la base de datos (usuarios en ab_user)
AUTH_TYPE = AUTH_DB

# --------------------------------------------------------------------------
# Base de datos MySQL (XAMPP o MySQL Workbench)
# --------------------------------------------------------------------------
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")  # si tu MySQL usa otro puerto (ej. 3307), cámbialo en .env
DB_NAME = os.getenv("DB_NAME", "biblioteca_db")

# DATABASE_URL tiene prioridad si quieres usar otra cadena completa
# (por ejemplo sqlite:///app.db para pruebas rápidas sin MySQL).
SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL") or (
    f"mysql+pymysql://{quote_plus(DB_USER)}:{quote_plus(DB_PASSWORD)}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
)
SQLALCHEMY_TRACK_MODIFICATIONS = False
# Evita el error "MySQL server has gone away" tras mucho tiempo inactivo
SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

# --------------------------------------------------------------------------
# Interfaz
# --------------------------------------------------------------------------
APP_NAME = "Biblioteca"
BABEL_DEFAULT_LOCALE = "es"
LANGUAGES = {
    "es": {"flag": "es", "name": "Español"},
    "en": {"flag": "gb", "name": "English"},
}

# --------------------------------------------------------------------------
# Asistente de IA (Groq, API compatible con OpenAI). La clave va en .env
# --------------------------------------------------------------------------
AI_PROVIDER = os.getenv("API_PROVIDER", "groq")
AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_MODEL = os.getenv("AI_MODEL", "openai/gpt-oss-20b")
AI_URL = os.getenv("AI_URL", "https://api.groq.com/openai/v1")
