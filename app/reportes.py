"""Tres reportes con consultas reales a la base de datos y filtros.

1. Libros más prestados     (filtros: fechas, categoría)
2. Préstamos vencidos       (filtros: socio, días mínimos de retraso)
3. Multas por socio         (filtros: estado de pago, fechas)

Cada reporte se puede imprimir/guardar como PDF desde el navegador y exportar a CSV.
"""
import csv
import io
from datetime import date, datetime, timedelta

from flask import Response, request
from flask_appbuilder import BaseView, expose, has_access
from sqlalchemy import case, func

from .extensions import appbuilder, db
from .models import Autor, Categoria, Libro, Multa, Prestamo, Socio

from .servicios import MULTA_POR_DIA  # noqa: E402


def _fecha(texto):
    """Convierte 'AAAA-MM-DD' en date; devuelve None si está vacío o es inválido."""
    try:
        return datetime.strptime(texto, "%Y-%m-%d").date() if texto else None
    except ValueError:
        return None


def _csv(nombre, columnas, filas):
    salida = io.StringIO()
    escritor = csv.writer(salida)
    escritor.writerow(columnas)
    escritor.writerows(filas)
    return Response("﻿" + salida.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": f"attachment; filename={nombre}.csv"})


class ReportesView(BaseView):
    route_base = "/reportes"
    default_view = "libros_mas_prestados"

    def _responder(self, nombre, titulo, descripcion, filtros, columnas, filas, barras=None):
        """Devuelve la página HTML o el CSV según ?formato=csv."""
        if request.args.get("formato") == "csv":
            return _csv(nombre, columnas, filas)
        self.update_redirect()
        return self.render_template(
            "reporte.html", titulo=titulo, descripcion=descripcion, filtros=filtros,
            columnas=columnas, filas=filas, barras=barras, hoy=date.today(),
            generado=datetime.now().strftime("%d/%m/%Y %H:%M"))

    # ------------------------------------------------------------------
    # 1. Libros más prestados
    # ------------------------------------------------------------------
    @expose("/libros-mas-prestados/")
    @has_access
    def libros_mas_prestados(self):
        desde = _fecha(request.args.get("desde"))
        hasta = _fecha(request.args.get("hasta"))
        categoria_id = request.args.get("categoria", type=int)

        total = func.count(Prestamo.id)
        q = (db.session.query(Libro.titulo, Autor.nombre, Categoria.nombre, total)
             .join(Prestamo, Prestamo.libro_id == Libro.id)
             .join(Autor, Libro.autor_id == Autor.id)
             .join(Categoria, Libro.categoria_id == Categoria.id))
        if desde:
            q = q.filter(Prestamo.fecha_prestamo >= desde)
        if hasta:
            q = q.filter(Prestamo.fecha_prestamo <= hasta)
        if categoria_id:
            q = q.filter(Libro.categoria_id == categoria_id)
        datos = (q.group_by(Libro.id, Libro.titulo, Autor.nombre, Categoria.nombre)
                 .order_by(total.desc(), Libro.titulo).limit(10).all())

        filas = [[i + 1, t, a, c, n] for i, (t, a, c, n) in enumerate(datos)]
        barras = [(t, n) for t, _a, _c, n in datos]
        cats = [(str(c.id), c.nombre) for c in db.session.query(Categoria).order_by(Categoria.nombre)]
        filtros = [
            {"name": "desde", "label": "Desde", "type": "date", "value": request.args.get("desde", "")},
            {"name": "hasta", "label": "Hasta", "type": "date", "value": request.args.get("hasta", "")},
            {"name": "categoria", "label": "Categoría", "type": "select",
             "value": request.args.get("categoria", ""), "options": [("", "Todas")] + cats},
        ]
        return self._responder(
            "libros_mas_prestados", "Libros más prestados",
            "Top 10 de libros con más préstamos en el rango de fechas elegido.",
            filtros, ["#", "Título", "Autor", "Categoría", "Préstamos"], filas, barras)

    # ------------------------------------------------------------------
    # 2. Préstamos vencidos
    # ------------------------------------------------------------------
    @expose("/prestamos-vencidos/")
    @has_access
    def prestamos_vencidos(self):
        texto = (request.args.get("socio") or "").strip()
        min_dias = request.args.get("min_dias", default=0, type=int) or 0
        hoy = date.today()

        q = (db.session.query(Prestamo).join(Socio).join(Libro)
             .filter(Prestamo.fecha_devolucion.is_(None), Prestamo.fecha_limite < hoy))
        if texto:
            patron = f"%{texto}%"
            q = q.filter((Socio.nombre.ilike(patron)) | (Socio.ci.ilike(patron)))
        if min_dias > 0:
            q = q.filter(Prestamo.fecha_limite <= hoy - timedelta(days=min_dias))
        prestamos = q.order_by(Prestamo.fecha_limite).all()

        filas = []
        for p in prestamos:
            retraso = (hoy - p.fecha_limite).days
            filas.append([p.socio.nombre, p.socio.ci, p.libro.titulo, p.fecha_limite.strftime("%d/%m/%Y"),
                          retraso, f"{retraso * float(MULTA_POR_DIA):.2f}"])
        barras = [(f"{f[0]} – {f[2]}", f[4]) for f in filas[:10]]
        filtros = [
            {"name": "socio", "label": "Socio (nombre o CI)", "type": "text", "value": texto},
            {"name": "min_dias", "label": "Mínimo de días de retraso", "type": "number",
             "value": request.args.get("min_dias", "")},
        ]
        return self._responder(
            "prestamos_vencidos", "Préstamos vencidos",
            "Préstamos no devueltos cuya fecha límite ya pasó, con los días de retraso y la multa estimada (Bs).",
            filtros, ["Socio", "CI", "Libro", "Fecha límite", "Días de retraso", "Multa estimada (Bs)"],
            filas, barras)

    # ------------------------------------------------------------------
    # 3. Multas por socio
    # ------------------------------------------------------------------
    @expose("/multas-por-socio/")
    @has_access
    def multas_por_socio(self):
        estado = request.args.get("estado", "")
        desde = _fecha(request.args.get("desde"))
        hasta = _fecha(request.args.get("hasta"))

        pagado = func.sum(case((Multa.pagada.is_(True), Multa.monto), else_=0))
        pendiente = func.sum(case((Multa.pagada.is_(False), Multa.monto), else_=0))
        q = (db.session.query(Socio.nombre, Socio.ci, func.count(Multa.id), func.sum(Multa.monto),
                              pagado, pendiente)
             .join(Prestamo, Prestamo.socio_id == Socio.id)
             .join(Multa, Multa.prestamo_id == Prestamo.id))
        if estado == "pagadas":
            q = q.filter(Multa.pagada.is_(True))
        elif estado == "pendientes":
            q = q.filter(Multa.pagada.is_(False))
        if desde:
            q = q.filter(Multa.fecha >= datetime.combine(desde, datetime.min.time()))
        if hasta:
            q = q.filter(Multa.fecha < datetime.combine(hasta + timedelta(days=1), datetime.min.time()))
        datos = (q.group_by(Socio.id, Socio.nombre, Socio.ci)
                 .order_by(func.sum(Multa.monto).desc()).all())

        filas = [[n, ci, c, f"{float(t or 0):.2f}", f"{float(pg or 0):.2f}", f"{float(pe or 0):.2f}"]
                 for n, ci, c, t, pg, pe in datos]
        barras = [(f[0], float(f[3])) for f in filas[:10]]
        filtros = [
            {"name": "estado", "label": "Estado", "type": "select", "value": estado,
             "options": [("", "Todas"), ("pendientes", "Pendientes"), ("pagadas", "Pagadas")]},
            {"name": "desde", "label": "Desde", "type": "date", "value": request.args.get("desde", "")},
            {"name": "hasta", "label": "Hasta", "type": "date", "value": request.args.get("hasta", "")},
        ]
        return self._responder(
            "multas_por_socio", "Multas por socio",
            "Total de multas de cada socio, separando lo pagado de lo pendiente (Bs).",
            filtros, ["Socio", "CI", "N.º de multas", "Total (Bs)", "Pagado (Bs)", "Pendiente (Bs)"],
            filas, barras)


appbuilder.add_view_no_menu(ReportesView)
appbuilder.add_link("Libros más prestados", href="/reportes/libros-mas-prestados/", icon="fa-trophy",
                    category="Reportes", category_icon="fa-bar-chart", baseview=ReportesView)
appbuilder.add_link("Préstamos vencidos", href="/reportes/prestamos-vencidos/", icon="fa-clock-o",
                    category="Reportes", baseview=ReportesView)
appbuilder.add_link("Multas por socio", href="/reportes/multas-por-socio/", icon="fa-money",
                    category="Reportes", baseview=ReportesView)
