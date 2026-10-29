"""Catálogo público: cualquier persona puede buscar libros sin iniciar sesión."""
from flask import abort, request
from flask_appbuilder import BaseView, expose
from sqlalchemy import or_

from .extensions import appbuilder, db
from .models import Autor, Categoria, Libro

POR_PAGINA = 15


class CatalogoView(BaseView):
    route_base = "/catalogo"
    default_view = "index"

    @expose("/")
    def index(self):
        texto = (request.args.get("q") or "").strip()
        cats = [c for c in request.args.getlist("categoria", type=int) if c]
        solo_disp = request.args.get("disponibles") == "1"
        desde = request.args.get("desde", type=int)
        hasta = request.args.get("hasta", type=int)
        pagina = max(request.args.get("pagina", default=1, type=int) or 1, 1)

        q = (db.session.query(Libro).join(Autor).join(Categoria).filter(Libro.activo.is_(True)))
        if texto:
            patron = f"%{texto}%"
            q = q.filter(or_(Libro.titulo.ilike(patron), Autor.nombre.ilike(patron),
                             Libro.isbn.ilike(patron), Categoria.nombre.ilike(patron)))
        if cats:
            q = q.filter(Libro.categoria_id.in_(cats))
        if solo_disp:
            q = q.filter(Libro.ejemplares_disponibles > 0)
        if desde:
            q = q.filter(Libro.anio_publicacion >= desde)
        if hasta:
            q = q.filter(Libro.anio_publicacion <= hasta)

        total = q.count()
        libros = q.order_by(Libro.titulo).offset((pagina - 1) * POR_PAGINA).limit(POR_PAGINA).all()
        paginas = max((total + POR_PAGINA - 1) // POR_PAGINA, 1)
        categorias = db.session.query(Categoria).order_by(Categoria.nombre).all()
        # Parámetros para los enlaces de paginación (sin 'pagina')
        args = [(k, v) for k, v in request.args.items(multi=True) if k != "pagina"]
        return self.render_template(
            "catalogo.html", libros=libros, total=total, texto=texto, cats=cats, solo_disp=solo_disp,
            desde=desde or "", hasta=hasta or "", pagina=pagina, paginas=paginas, categorias=categorias,
            args=args)

    @expose("/libro/<int:pk>")
    def libro(self, pk):
        libro = db.session.get(Libro, pk)
        if libro is None or not libro.activo:
            abort(404)
        return self.render_template("libro.html", libro=libro)


appbuilder.add_view_no_menu(CatalogoView)
