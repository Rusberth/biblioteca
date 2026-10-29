"""Fábrica de la aplicación Flask AppBuilder."""
import logging

from flask import Flask

from .extensions import appbuilder, db

logging.basicConfig(format="%(asctime)s:%(levelname)s:%(name)s:%(message)s")
logging.getLogger().setLevel(logging.INFO)


def create_app(config_object: str = "config") -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_object)

    db.init_app(app)
    with app.app_context():
        appbuilder.init_app(app, db.session)
        # Importar aquí registra los modelos y las vistas (menú).
        from . import models, views  # noqa: F401

    return app


# `app` a nivel de módulo para poder usar: from app import app
app = create_app()
