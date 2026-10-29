"""Agrega datos de ejemplo para que los reportes tengan contenido.

Uso:  python seed.py   (primero)   y luego   python seed_reportes.py
Es seguro ejecutarlo una sola vez; si ya hay muchos préstamos no hace nada.
"""
import random
from datetime import date, datetime, timedelta
from decimal import Decimal

from app import app, db
from app.models import Autor, Categoria, Libro, Multa, Prestamo, Socio

random.seed(7)

with app.app_context():
    if db.session.query(Prestamo).count() > 5:
        print("Ya hay datos para los reportes; no se agrega nada.")
        raise SystemExit
    if db.session.query(Libro).count() == 0:
        print("Primero ejecuta: python seed.py")
        raise SystemExit

    extra_libros = [
        ("El principito", "9780156012195", 1943, "Novela", "Antoine de Saint-Exupéry", "Francia"),
        ("Breve historia del tiempo", "9780553380163", 1988, "Ciencia", "Stephen Hawking", "Reino Unido"),
        ("Python para todos", "9781449355739", 2015, "Programación", "Charles Severance", "Estados Unidos"),
        ("La casa de los espíritus", "9780553383805", 1982, "Novela", "Isabel Allende", "Chile"),
    ]
    for titulo, isbn, anio, cat, autor, pais in extra_libros:
        c = db.session.query(Categoria).filter_by(nombre=cat).first()
        a = db.session.query(Autor).filter_by(nombre=autor).first() or Autor(nombre=autor, nacionalidad=pais)
        db.session.add(a)
        if not db.session.query(Libro).filter_by(isbn=isbn).first():
            db.session.add(Libro(titulo=titulo, isbn=isbn, anio_publicacion=anio, categoria=c, autor=a,
                                 ejemplares_total=3, ejemplares_disponibles=3))
    for nombre, ci in [("María Quispe", "5551234"), ("Carlos Mamani", "4449876"), ("Lucía Flores", "6663210")]:
        if not db.session.query(Socio).filter_by(ci=ci).first():
            db.session.add(Socio(nombre=nombre, ci=ci, email=f"{ci}@mail.com"))
    db.session.flush()

    libros = db.session.query(Libro).all()
    socios = db.session.query(Socio).all()
    hoy = date.today()
    pesos = [5 if l.titulo in ("Cien años de soledad", "Cosmos") else 2 for l in libros]

    for _ in range(30):                      # historial devuelto (algunos con retraso y multa)
        libro = random.choices(libros, weights=pesos)[0]
        socio = random.choice(socios)
        inicio = hoy - timedelta(days=random.randint(20, 150))
        limite = inicio + timedelta(days=14)
        retraso = random.choice([0, 0, 0, 3, 7, 12])
        devol = limite + timedelta(days=retraso)
        p = Prestamo(libro=libro, socio=socio, fecha_prestamo=inicio, fecha_limite=limite,
                     fecha_devolucion=devol, estado="Devuelto")
        db.session.add(p)
        if retraso:
            db.session.add(Multa(prestamo=p, monto=Decimal(retraso), motivo=f"Retraso de {retraso} día(s)",
                                 pagada=random.random() < 0.5,
                                 fecha=datetime.combine(devol, datetime.min.time())))
    for socio in socios[:3]:                 # algunos préstamos vencidos sin devolver
        libro = random.choice(libros)
        inicio = hoy - timedelta(days=random.randint(20, 45))
        db.session.add(Prestamo(libro=libro, socio=socio, fecha_prestamo=inicio,
                                fecha_limite=inicio + timedelta(days=14), estado="Activo"))
        libro.ejemplares_disponibles = max(0, libro.ejemplares_disponibles - 1)
    db.session.commit()
    print("Datos de ejemplo para reportes cargados.")
