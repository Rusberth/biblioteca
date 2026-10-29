"""Datos de ejemplo (opcional): python seed.py"""
from datetime import date, timedelta

from app import app, db
from app.models import Autor, Categoria, Libro, Prestamo, Socio

with app.app_context():
    if db.session.query(Categoria).count():
        print("Ya hay datos; no se agrega nada.")
        raise SystemExit
    cats = {n: Categoria(nombre=n) for n in ["Novela", "Ciencia", "Historia", "Programación"]}
    aut = {n: Autor(nombre=n, nacionalidad=p) for n, p in [
        ("Gabriel García Márquez", "Colombia"), ("Carl Sagan", "Estados Unidos"),
        ("Eduardo Galeano", "Uruguay"), ("Robert C. Martin", "Estados Unidos")]}
    db.session.add_all(list(cats.values()) + list(aut.values()))
    libros = [
        Libro(titulo="Cien años de soledad", isbn="9780307474728", anio_publicacion=1967,
              categoria=cats["Novela"], autor=aut["Gabriel García Márquez"], ejemplares_total=3, ejemplares_disponibles=3),
        Libro(titulo="Cosmos", isbn="9780345539434", anio_publicacion=1980,
              categoria=cats["Ciencia"], autor=aut["Carl Sagan"], ejemplares_total=2, ejemplares_disponibles=2),
        Libro(titulo="Las venas abiertas de América Latina", isbn="9788432312038", anio_publicacion=1971,
              categoria=cats["Historia"], autor=aut["Eduardo Galeano"], ejemplares_total=2, ejemplares_disponibles=2),
        Libro(titulo="Clean Code", isbn="9780132350884", anio_publicacion=2008,
              categoria=cats["Programación"], autor=aut["Robert C. Martin"], ejemplares_total=1, ejemplares_disponibles=1),
    ]
    socios = [Socio(nombre="Ana Pérez", ci="1234567", email="ana@mail.com"),
              Socio(nombre="Luis Rojas", ci="7654321", email="luis@mail.com")]
    db.session.add_all(libros + socios)
    db.session.flush()
    hoy = date.today()
    # préstamo vencido (para probar reportes y multas)
    libros[0].ejemplares_disponibles -= 1
    db.session.add(Prestamo(libro=libros[0], socio=socios[0], fecha_prestamo=hoy - timedelta(days=30),
                            fecha_limite=hoy - timedelta(days=16), estado="Activo"))
    db.session.commit()
    print("Datos de ejemplo cargados.")
