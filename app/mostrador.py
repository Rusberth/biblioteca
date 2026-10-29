"""Mostrador: prestar y devolver en una sola pantalla + carnet imprimible del socio."""
from datetime import date

from flask import g, jsonify, request
from flask_appbuilder import BaseView, expose, has_access
from flask_wtf.csrf import generate_csrf
from sqlalchemy import or_

from . import servicios
from .extensions import appbuilder, db
from .models import Autor, Libro, Prestamo, Socio


def _prestamo_json(p):
    return {"id": p.id, "libro": p.libro.titulo, "limite": p.fecha_limite.strftime("%d/%m/%Y"),
            "vencido": p.vencido,
            "dias": (date.today() - p.fecha_limite).days if p.vencido else 0}


class MostradorView(BaseView):
    route_base = "/mostrador"
    default_view = "pantalla"

    @expose("/")
    @has_access
    def pantalla(self):
        self.update_redirect()
        return self.render_template("mostrador.html", csrf_token_valor=generate_csrf())

    @expose("/socio")
    @has_access
    def socio(self):
        ci = (request.args.get("ci") or "").strip()
        s = db.session.query(Socio).filter(Socio.ci == ci).first() if ci else None
        if not s:
            return jsonify({"error": "No existe un socio con ese CI"}), 404
        activos = [p for p in s.prestamos if p.estado == "Activo"]
        pendientes = [m for p in s.prestamos for m in p.multas if not m.pagada]
        return jsonify({
            "id": s.id, "nombre": s.nombre, "ci": s.ci, "activo": s.activo,
            "prestamos": [_prestamo_json(p) for p in activos],
            "multas": float(sum(m.monto for m in pendientes)),
        })

    @expose("/libros")
    @has_access
    def libros(self):
        texto = (request.args.get("q") or "").strip()
        if len(texto) < 2:
            return jsonify([])
        patron = f"%{texto}%"
        encontrados = (db.session.query(Libro).join(Autor).filter(Libro.activo.is_(True))
                       .filter(or_(Libro.titulo.ilike(patron), Libro.isbn.ilike(patron),
                                   Autor.nombre.ilike(patron)))
                       .order_by(Libro.titulo).limit(8).all())
        return jsonify([{"id": l.id, "titulo": l.titulo, "autor": l.autor.nombre,
                         "disponibles": l.ejemplares_disponibles} for l in encontrados])

    @expose("/prestar", methods=["POST"])
    @has_access
    def prestar(self):
        datos = request.get_json(silent=True) or {}
        libro = db.session.get(Libro, datos.get("libro_id"))
        socio = db.session.get(Socio, datos.get("socio_id"))
        try:
            p = Prestamo(libro=libro, socio=socio)
            servicios.preparar_prestamo(p, g.user.id)
        except ValueError as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 400
        db.session.add(p)
        db.session.commit()
        return jsonify({"ok": f"Prestado «{libro.titulo}» a {socio.nombre}. Devolver antes del "
                              f"{p.fecha_limite.strftime('%d/%m/%Y')}."})

    @expose("/devolver", methods=["POST"])
    @has_access
    def devolver(self):
        datos = request.get_json(silent=True) or {}
        p = db.session.get(Prestamo, datos.get("prestamo_id"))
        if not p:
            return jsonify({"error": "Préstamo no encontrado"}), 404
        try:
            retraso, multa = servicios.devolver_prestamo(p)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        db.session.commit()
        msg = f"Devuelto «{p.libro.titulo}»."
        if multa:
            msg += f" Retraso de {retraso} día(s): multa de Bs {multa.monto}."
        return jsonify({"ok": msg})


class CarnetView(BaseView):
    route_base = "/carnet"

    @expose("/<int:pk>")
    @has_access
    def carnet(self, pk):
        socio = db.session.get(Socio, pk)
        if not socio:
            return "Socio no encontrado", 404
        return self.render_template("carnet.html", socio=socio)


appbuilder.add_view(MostradorView, "Mostrador", icon="fa-cash-register", category="Circulación")
appbuilder.add_view_no_menu(CarnetView)
