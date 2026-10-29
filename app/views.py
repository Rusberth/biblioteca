"""Vistas CRUD, menú y lógica de préstamos de la biblioteca."""
from flask import flash, g, redirect, url_for
from flask_appbuilder import ModelView, action
from flask_appbuilder.models.sqla.interface import SQLAInterface
from wtforms.validators import NumberRange

from . import servicios
from .extensions import appbuilder, db
from .models import Autor, Categoria, Libro, Multa, Prestamo, Socio


def si_no(valor):
    return "Sí" if valor else "No"


class CategoriaView(ModelView):
    datamodel = SQLAInterface(Categoria)
    list_title = "Lista de categorías"
    show_title = "Detalle de la categoría"
    add_title = "Agregar categoría"
    edit_title = "Editar categoría"
    label_columns = {"nombre": "Nombre", "descripcion": "Descripción"}
    list_columns = ["nombre", "descripcion"]
    add_columns = edit_columns = ["nombre", "descripcion"]
    search_columns = ["nombre"]
    base_order = ("nombre", "asc")


class AutorView(ModelView):
    datamodel = SQLAInterface(Autor)
    list_title = "Lista de autores"
    show_title = "Detalle del autor"
    add_title = "Agregar autor"
    edit_title = "Editar autor"
    label_columns = {"nombre": "Nombre", "nacionalidad": "Nacionalidad"}
    list_columns = ["nombre", "nacionalidad"]
    add_columns = edit_columns = ["nombre", "nacionalidad"]
    search_columns = ["nombre", "nacionalidad"]
    base_order = ("nombre", "asc")


class LibroView(ModelView):
    datamodel = SQLAInterface(Libro)
    list_title = "Catálogo de libros"
    show_title = "Detalle del libro"
    add_title = "Agregar libro"
    edit_title = "Editar libro"
    label_columns = {
        "titulo": "Título", "isbn": "ISBN", "anio_publicacion": "Año",
        "categoria": "Categoría", "autor": "Autor",
        "ejemplares_total": "Ejemplares", "ejemplares_disponibles": "Disponibles",
        "disponibilidad": "Estado", "activo": "Activo",
    }
    list_columns = ["titulo", "autor", "categoria", "ejemplares_disponibles", "disponibilidad"]
    show_columns = ["titulo", "isbn", "anio_publicacion", "autor", "categoria",
                    "ejemplares_total", "ejemplares_disponibles", "activo"]
    add_columns = edit_columns = ["titulo", "isbn", "anio_publicacion", "autor",
                                  "categoria", "ejemplares_total", "ejemplares_disponibles", "activo"]
    search_columns = ["titulo", "isbn", "autor", "categoria", "activo"]
    base_order = ("titulo", "asc")
    formatters_columns = {"activo": si_no}
    validators_columns = {
        "ejemplares_total": [NumberRange(min=0, message="No puede ser negativo")],
        "ejemplares_disponibles": [NumberRange(min=0, message="No puede ser negativo")],
    }


class SocioView(ModelView):
    datamodel = SQLAInterface(Socio)
    list_title = "Lista de socios"
    show_title = "Detalle del socio"
    add_title = "Agregar socio"
    edit_title = "Editar socio"
    label_columns = {"nombre": "Nombre", "ci": "CI", "email": "Correo",
                     "telefono": "Teléfono", "fecha_registro": "Registro", "activo": "Activo"}
    list_columns = ["nombre", "ci", "email", "telefono", "activo"]
    add_columns = edit_columns = ["nombre", "ci", "email", "telefono", "activo"]
    show_columns = ["nombre", "ci", "email", "telefono", "fecha_registro", "activo"]
    search_columns = ["nombre", "ci", "email", "activo"]
    base_order = ("nombre", "asc")
    formatters_columns = {"activo": si_no}

    @action("carnet", "Ver carnet", "", "fa-id-card", multiple=True, single=True)
    def carnet(self, items):
        item = items[0] if isinstance(items, (list, tuple)) else items
        return redirect(url_for("CarnetView.carnet", pk=item.id))


class PrestamoView(ModelView):
    datamodel = SQLAInterface(Prestamo)
    list_title = "Lista de préstamos"
    show_title = "Detalle del préstamo"
    add_title = "Registrar préstamo"
    edit_title = "Editar préstamo"
    label_columns = {
        "libro": "Libro", "socio": "Socio", "usuario": "Registrado por",
        "fecha_prestamo": "Fecha de préstamo", "fecha_limite": "Fecha límite",
        "fecha_devolucion": "Fecha de devolución", "estado": "Estado",
    }
    list_columns = ["id", "libro", "socio", "fecha_prestamo", "fecha_limite", "estado"]
    show_columns = ["libro", "socio", "usuario", "fecha_prestamo", "fecha_limite",
                    "fecha_devolucion", "estado"]
    add_columns = ["libro", "socio"]          # lo demás se completa solo
    edit_columns = ["fecha_limite"]
    search_columns = ["libro", "socio", "estado", "fecha_prestamo"]
    base_order = ("id", "desc")

    def pre_add(self, item):
        servicios.preparar_prestamo(item, g.user.id)

    @action("devolver", "Registrar devolución", "¿Registrar la devolución?",
            "fa-undo", multiple=True, single=True)
    def devolver(self, items):
        # Desde la lista FAB entrega una lista; desde el detalle, un solo objeto.
        if not isinstance(items, (list, tuple)):
            items = [items]
        for item in items:
            self._devolver_uno(item)
        db.session.commit()
        return redirect(url_for("PrestamoView.list"))

    def _devolver_uno(self, item):
        try:
            retraso, multa = servicios.devolver_prestamo(item)
        except ValueError as e:
            flash(str(e), "warning")
            return
        if multa:
            flash(f"Préstamo #{item.id} devuelto con retraso: multa de Bs {multa.monto}", "warning")
        else:
            flash(f"Préstamo #{item.id}: devolución registrada.", "success")


class MultaView(ModelView):
    datamodel = SQLAInterface(Multa)
    list_title = "Lista de multas"
    show_title = "Detalle de la multa"
    add_title = "Agregar multa"
    edit_title = "Editar multa"
    label_columns = {"prestamo": "Préstamo", "monto": "Monto (Bs)", "motivo": "Motivo",
                     "pagada": "Pagada", "fecha": "Fecha"}
    list_columns = ["prestamo", "monto", "motivo", "pagada", "fecha"]
    add_columns = edit_columns = ["prestamo", "monto", "motivo", "pagada"]
    search_columns = ["prestamo", "pagada", "fecha"]
    base_order = ("fecha", "desc")
    formatters_columns = {"pagada": si_no}
    validators_columns = {"monto": [NumberRange(min=0, message="No puede ser negativo")]}

    @action("pagar", "Marcar como pagada", "¿Marcar las multas seleccionadas como pagadas?",
            "fa-check", multiple=True, single=True)
    def pagar(self, items):
        items = items if isinstance(items, (list, tuple)) else [items]
        cobradas = 0
        for multa in items:
            if not multa.pagada:
                multa.pagada = True
                cobradas += 1
        db.session.commit()
        flash(f"{cobradas} multa(s) marcada(s) como pagada(s).", "success")
        return redirect(url_for("MultaView.list"))



appbuilder.add_view(LibroView, "Libros", icon="fa-book", category="Catálogo")
appbuilder.add_view(AutorView, "Autores", icon="fa-user", category="Catálogo")
appbuilder.add_view(CategoriaView, "Categorías", icon="fa-folder-open", category="Catálogo")
appbuilder.add_view(SocioView, "Socios", icon="fa-users", category="Circulación")
appbuilder.add_view(PrestamoView, "Préstamos", icon="fa-exchange", category="Circulación")
appbuilder.add_view(MultaView, "Multas", icon="fa-money", category="Circulación")

# El asistente de IA se registra al final para que aparezca en el menú
from .asistente import AsistenteView  # noqa: E402

appbuilder.add_view(AsistenteView, "Asistente IA", icon="fa-comments", category="Asistente")

# Reportes (3 consultas con filtros)
from . import reportes  # noqa: E402,F401

# Rediseño: catálogo público, mostrador y carnet
from . import catalogo, mostrador  # noqa: E402,F401
