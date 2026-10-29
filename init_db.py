"""Crea en MySQL las tablas de FAB (ab_*) y las de nuestros modelos.

Antes: crear la base VACÍA biblioteca_db en phpMyAdmin.
Uso:  python init_db.py
"""
from flask_appbuilder import Model
from sqlalchemy import inspect
from sqlalchemy.exc import OperationalError

from app import app, db
from app import models  # noqa: F401  (registra los modelos)

with app.app_context():
    try:
        Model.metadata.create_all(bind=db.engine)
    except OperationalError as error:
        print("No se pudo conectar con la base de datos.")
        print("Revisa que MySQL esté iniciado en XAMPP, el puerto y que la base exista.")
        print(f"Detalle: {error.orig}")
        raise SystemExit(1)

    print("Tablas en la base de datos:")
    for tabla in sorted(inspect(db.engine).get_table_names()):
        print("--", tabla)
    print("creado correctamente")
