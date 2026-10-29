"""Genera datos de prueba para no llenar nada a mano.

Crea categorías, autores, libros, socios, préstamos (con historial de 6 meses),
multas (pagadas y pendientes) y dos usuarios del sistema para probar los roles.

Uso (después de init_db.py e init_roles.py):
    python datos_prueba.py            # agrega lo que falte (se puede repetir)
    python datos_prueba.py --limpiar  # borra libros/socios/préstamos/multas y vuelve a generar

Los ISBN son códigos de ejemplo, no corresponden a ediciones reales.
Usuarios de prueba:  bibliotecaria / Biblio123*   (rol Bibliotecario)
                     lector / Lector123*          (rol Consulta)
"""
import random
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal

from app import app, db
from app.models import Autor, Categoria, Libro, Multa, Prestamo, Socio

random.seed(2026)
HOY = date.today()

# (título, autor, país del autor, categoría, año)
LIBROS = [
    ("Cien años de soledad", "Gabriel García Márquez", "Colombia", "Novela", 1967),
    ("El amor en los tiempos del cólera", "Gabriel García Márquez", "Colombia", "Novela", 1985),
    ("La casa de los espíritus", "Isabel Allende", "Chile", "Novela", 1982),
    ("Rayuela", "Julio Cortázar", "Argentina", "Novela", 1963),
    ("Pedro Páramo", "Juan Rulfo", "México", "Novela", 1955),
    ("La ciudad y los perros", "Mario Vargas Llosa", "Perú", "Novela", 1963),
    ("Don Quijote de la Mancha", "Miguel de Cervantes", "España", "Novela", 1605),
    ("El túnel", "Ernesto Sabato", "Argentina", "Novela", 1948),
    ("Aluvión de fuego", "Oscar Cerruto", "Bolivia", "Novela", 1935),
    ("Juan de la Rosa", "Nataniel Aguirre", "Bolivia", "Novela", 1885),
    ("Los deshabitados", "Marcelo Quiroga Santa Cruz", "Bolivia", "Novela", 1959),
    ("Ficciones", "Jorge Luis Borges", "Argentina", "Cuento", 1944),
    ("El Aleph", "Jorge Luis Borges", "Argentina", "Cuento", 1949),
    ("Cuentos de la selva", "Horacio Quiroga", "Uruguay", "Cuento", 1918),
    ("Doce cuentos peregrinos", "Gabriel García Márquez", "Colombia", "Cuento", 1992),
    ("Veinte poemas de amor y una canción desesperada", "Pablo Neruda", "Chile", "Poesía", 1924),
    ("Rimas y leyendas", "Gustavo Adolfo Bécquer", "España", "Poesía", 1871),
    ("Trilce", "César Vallejo", "Perú", "Poesía", 1922),
    ("Cosmos", "Carl Sagan", "Estados Unidos", "Ciencia", 1980),
    ("Breve historia del tiempo", "Stephen Hawking", "Reino Unido", "Ciencia", 1988),
    ("El gen egoísta", "Richard Dawkins", "Reino Unido", "Ciencia", 1976),
    ("El origen de las especies", "Charles Darwin", "Reino Unido", "Ciencia", 1859),
    ("Una breve historia de casi todo", "Bill Bryson", "Estados Unidos", "Ciencia", 2003),
    ("Las venas abiertas de América Latina", "Eduardo Galeano", "Uruguay", "Historia", 1971),
    ("Armas, gérmenes y acero", "Jared Diamond", "Estados Unidos", "Historia", 1997),
    ("Sapiens", "Yuval Noah Harari", "Israel", "Historia", 2011),
    ("Historia de Bolivia", "Herbert Klein", "Estados Unidos", "Historia", 1982),
    ("Clean Code", "Robert C. Martin", "Estados Unidos", "Programación", 2008),
    ("Python para todos", "Charles Severance", "Estados Unidos", "Programación", 2015),
    ("The Pragmatic Programmer", "Andrew Hunt", "Estados Unidos", "Programación", 1999),
    ("Introduction to Algorithms", "Thomas H. Cormen", "Estados Unidos", "Programación", 1990),
    ("Diseño de bases de datos", "Carlos Coronel", "Estados Unidos", "Programación", 2011),
    ("Flask Web Development", "Miguel Grinberg", "Estados Unidos", "Programación", 2014),
    ("Álgebra", "Aurelio Baldor", "Cuba", "Matemáticas", 1941),
    ("Cálculo", "James Stewart", "Canadá", "Matemáticas", 1987),
    ("El hombre que calculaba", "Malba Tahan", "Brasil", "Matemáticas", 1938),
    ("Matemáticas discretas", "Kenneth Rosen", "Estados Unidos", "Matemáticas", 1988),
    ("La República", "Platón", "Grecia", "Filosofía", -380),
    ("Meditaciones", "Marco Aurelio", "Roma", "Filosofía", 180),
    ("Así habló Zaratustra", "Friedrich Nietzsche", "Alemania", "Filosofía", 1883),
    ("El mundo de Sofía", "Jostein Gaarder", "Noruega", "Filosofía", 1991),
    ("El principito", "Antoine de Saint-Exupéry", "Francia", "Infantil", 1943),
    ("Alicia en el país de las maravillas", "Lewis Carroll", "Reino Unido", "Infantil", 1865),
    ("Momo", "Michael Ende", "Alemania", "Infantil", 1973),
    ("La historia interminable", "Michael Ende", "Alemania", "Infantil", 1979),
    ("Diario de Ana Frank", "Ana Frank", "Alemania", "Biografía", 1947),
    ("Long Walk to Freedom", "Nelson Mandela", "Sudáfrica", "Biografía", 1994),
    ("Steve Jobs", "Walter Isaacson", "Estados Unidos", "Biografía", 2011),
    ("Confieso que he vivido", "Pablo Neruda", "Chile", "Biografía", 1974),
]
NOMBRES = ["Ana", "Luis", "María", "Carlos", "Lucía", "Jorge", "Sofía", "Diego", "Valeria", "Marco", "Camila",
           "Andrés", "Daniela", "Pablo", "Fernanda", "Rodrigo", "Gabriela", "Mateo", "Paola", "Sergio",
           "Carla", "Iván", "Rosa", "Hugo", "Elena"]
APELLIDOS = ["Quispe", "Mamani", "Flores", "Rojas", "Condori", "Vargas", "Choque", "Gutiérrez", "Villca",
             "Fernández", "Copa", "Mendoza", "Ticona", "Arce", "Soliz", "Rivera", "Cruz", "Limachi"]


def obtener(modelo, **claves):
    obj = db.session.query(modelo).filter_by(**claves).first()
    return obj, obj is None


def crear_usuarios(sm):
    biblio_id = None
    for usuario, nombre, apellido, rol, clave in [
        ("bibliotecaria", "Beatriz", "Rojas", "Bibliotecario", "Biblio123*"),
        ("lector", "Luis", "Consulta", "Consulta", "Lector123*"),
    ]:
        existente = sm.find_user(usuario)
        if not existente:
            role = sm.find_role(rol)
            if role is None:
                print(f"Falta el rol {rol}. Ejecuta antes: python init_roles.py")
                raise SystemExit(1)
            existente = sm.add_user(usuario, nombre, apellido, f"{usuario}@biblioteca.test", role, password=clave)
            print(f"  usuario creado: {usuario}")
        if usuario == "bibliotecaria" and existente:
            biblio_id = existente.id
    return biblio_id


with app.app_context():
    if "--limpiar" in sys.argv:
        for m in (Multa, Prestamo, Libro, Socio):
            db.session.query(m).delete()
        db.session.commit()
        print("Datos anteriores borrados.")

    biblio_id = crear_usuarios(app.appbuilder.sm)

    # Categorías, autores y libros
    nuevos = 0
    cats, autores = {}, {}
    for titulo, autor, pais, cat, anio in LIBROS:
        if cat not in cats:
            cats[cat], creado = obtener(Categoria, nombre=cat)
            if creado:
                cats[cat] = Categoria(nombre=cat, descripcion=f"Libros de {cat.lower()}")
                db.session.add(cats[cat])
        if autor not in autores:
            autores[autor], creado = obtener(Autor, nombre=autor)
            if creado:
                autores[autor] = Autor(nombre=autor, nacionalidad=pais)
                db.session.add(autores[autor])
    db.session.flush()
    for i, (titulo, autor, pais, cat, anio) in enumerate(LIBROS):
        isbn = f"978-99905-{i:03d}-{(i * 7) % 10}"
        existente, creado = obtener(Libro, isbn=isbn)
        if creado:
            total = random.choice([1, 2, 2, 3, 3, 4, 5])
            db.session.add(Libro(titulo=titulo, isbn=isbn, anio_publicacion=anio if anio > 0 else None,
                                 categoria=cats[cat], autor=autores[autor],
                                 ejemplares_total=total, ejemplares_disponibles=total))
            nuevos += 1
    # Socios
    socios_nuevos = 0
    usados = {s.ci for s in db.session.query(Socio.ci)}
    while db.session.query(Socio).count() + 0 < 45 and socios_nuevos < 45:
        ci = str(random.randint(3000000, 9999999))
        if ci in usados:
            continue
        usados.add(ci)
        nombre = f"{random.choice(NOMBRES)} {random.choice(APELLIDOS)} {random.choice(APELLIDOS)}"
        db.session.add(Socio(nombre=nombre, ci=ci, email=f"{ci}@correo.test",
                             telefono=f"7{random.randint(1000000, 9999999)}",
                             fecha_registro=HOY - timedelta(days=random.randint(30, 400)),
                             activo=random.random() > 0.06))
        socios_nuevos += 1
        db.session.flush()
    db.session.commit()

    # Préstamos y multas (solo si todavía hay pocos)
    if db.session.query(Prestamo).count() < 40:
        libros = db.session.query(Libro).all()
        socios = [s for s in db.session.query(Socio).all() if s.activo]
        populares = set(random.sample(libros, 8))
        pesos = [6 if l in populares else 1 for l in libros]
        creados = 0
        for _ in range(230):                      # historial devuelto
            libro = random.choices(libros, weights=pesos)[0]
            socio = random.choice(socios)
            inicio = HOY - timedelta(days=random.randint(16, 180))
            limite = inicio + timedelta(days=14)
            retraso = random.choices([0, 1, 3, 5, 9, 15], weights=[62, 8, 10, 8, 7, 5])[0]
            devol = limite + timedelta(days=retraso) if retraso else inicio + timedelta(days=random.randint(2, 14))
            p = Prestamo(libro=libro, socio=socio, usuario_id=biblio_id, fecha_prestamo=inicio,
                         fecha_limite=limite, fecha_devolucion=devol, estado="Devuelto")
            db.session.add(p)
            if retraso:
                db.session.add(Multa(prestamo=p, monto=Decimal(retraso), motivo=f"Retraso de {retraso} día(s)",
                                     pagada=random.random() < 0.6,
                                     fecha=datetime.combine(devol, datetime.min.time())))
            creados += 1
        # Activos: 6 vencidos, 4 por vencer, 8 vigentes
        for dias_restantes in [-18, -12, -9, -6, -3, -1, 0, 1, 2, 3, 5, 7, 8, 9, 10, 11, 12, 13]:
            libro = random.choice(libros)
            limite = HOY + timedelta(days=dias_restantes)
            db.session.add(Prestamo(libro=libro, socio=random.choice(socios), usuario_id=biblio_id,
                                    fecha_prestamo=limite - timedelta(days=14), fecha_limite=limite,
                                    estado="Activo"))
            creados += 1
        db.session.flush()
        print(f"  préstamos creados: {creados}")

    # Stock coherente: disponibles = total - préstamos activos (nunca negativo)
    db.session.flush()
    for libro in db.session.query(Libro).all():
        activos = db.session.query(Prestamo).filter_by(libro_id=libro.id, estado="Activo").count()
        libro.ejemplares_total = max(libro.ejemplares_total, activos)
        libro.ejemplares_disponibles = libro.ejemplares_total - activos
    db.session.commit()

    print("Listo. Totales:",
          {n: db.session.query(m).count() for n, m in
           [("categorías", Categoria), ("autores", Autor), ("libros", Libro), ("socios", Socio),
            ("préstamos", Prestamo), ("multas", Multa)]})
