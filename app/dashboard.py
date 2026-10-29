"""Panel de inicio: indicadores y gráficos de la biblioteca."""
from collections import Counter
from datetime import date, timedelta

from flask import redirect, url_for
from flask_appbuilder import IndexView, expose
from flask_login import current_user
from sqlalchemy import func

from .extensions import db
from .models import Categoria, Libro, Multa, Prestamo, Socio

MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


def ultimos_meses(n=6):
    """Lista de (año, mes) de los últimos n meses, del más antiguo al actual."""
    hoy = date.today()
    y, m = hoy.year, hoy.month
    salida = []
    for _ in range(n):
        salida.append((y, m))
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    return list(reversed(salida))


def datos_panel(ver_socios):
    hoy = date.today()
    q = db.session.query
    datos = {
        "libros": q(Libro).filter(Libro.activo.is_(True)).count(),
        "disponibles": int(q(func.coalesce(func.sum(Libro.ejemplares_disponibles), 0)).scalar() or 0),
        "socios": q(Socio).filter(Socio.activo.is_(True)).count(),
        "activos": q(Prestamo).filter(Prestamo.estado == "Activo").count(),
        "vencidos": q(Prestamo).filter(Prestamo.estado == "Activo", Prestamo.fecha_limite < hoy).count(),
        "multas_pendientes": float(q(func.coalesce(func.sum(Multa.monto), 0))
                                   .filter(Multa.pagada.is_(False)).scalar() or 0),
        "ver_socios": ver_socios,
    }
    # Préstamos por mes (últimos 6)
    meses = ultimos_meses(6)
    cuenta = Counter((p.fecha_prestamo.year, p.fecha_prestamo.month)
                     for p in q(Prestamo.fecha_prestamo).filter(
                         Prestamo.fecha_prestamo >= date(meses[0][0], meses[0][1], 1)))
    datos["por_mes"] = {"etiquetas": [MESES[m - 1] for _y, m in meses],
                        "valores": [cuenta.get(k, 0) for k in meses]}
    # Préstamos por categoría
    filas = (q(Categoria.nombre, func.count(Prestamo.id), Categoria.id)
             .join(Libro, Libro.categoria_id == Categoria.id)
             .join(Prestamo, Prestamo.libro_id == Libro.id)
             .group_by(Categoria.id, Categoria.nombre).order_by(func.count(Prestamo.id).desc()).all())
    datos["por_categoria"] = {"etiquetas": [f[0] for f in filas], "valores": [f[1] for f in filas],
                              "colores": [f[2] % 8 for f in filas]}
    datos["agotados"] = q(Libro).filter(Libro.activo.is_(True), Libro.ejemplares_disponibles <= 0).count()
    datos["novedades"] = q(Libro).order_by(Libro.id.desc()).limit(6).all()
    if ver_socios:
        limite = hoy + timedelta(days=3)
        datos["por_vencer"] = q(Prestamo).filter(Prestamo.estado == "Activo", Prestamo.fecha_limite >= hoy,
                                                  Prestamo.fecha_limite <= limite).count()
        datos["recientes"] = q(Prestamo).order_by(Prestamo.id.desc()).limit(8).all()
        alertas = (db.session.query(Prestamo).filter(Prestamo.estado == "Activo", Prestamo.fecha_limite <= limite)
                   .order_by(Prestamo.fecha_limite).limit(8).all())
        datos["alertas"] = [{
            "socio": p.socio.nombre, "libro": p.libro.titulo, "limite": p.fecha_limite.strftime("%d/%m/%Y"),
            "dias": (hoy - p.fecha_limite).days} for p in alertas]
    else:
        datos["alertas"] = []
    return datos


class PanelView(IndexView):
    index_template = "panel.html"

    @expose("/")
    def index(self):
        if current_user.is_anonymous:
            return redirect(url_for("CatalogoView.index"))
        self.update_redirect()
        ver_socios = self.appbuilder.sm.has_access("can_list", "SocioView")
        return self.render_template(self.index_template, appbuilder=self.appbuilder,
                                    d=datos_panel(ver_socios))
