"""Extensiones compartidas de la aplicación.

Se definen aquí (y no en __init__.py) para evitar importaciones circulares:
models.py y views.py importan desde este archivo.
"""
from flask_appbuilder import AppBuilder
from flask_appbuilder.utils.legacy import get_sqla_class

# SQLA de Flask-AppBuilder: es el SQLAlchemy de Flask extendido para que
# db.create_all() conozca también las tablas propias de FAB (ab_user, ab_role...).
SQLA = get_sqla_class()

db = SQLA()
appbuilder = AppBuilder()
