# Documentación del sistema Biblioteca

Proyecto individual del examen de *Taller de aplicaciones en Internet* (UAB).
Aplicación web de gestión de biblioteca hecha con **Flask AppBuilder + Python + MySQL**.

## 1. Qué hace el sistema
Permite registrar libros, autores, categorías y socios; prestar y devolver libros; cobrar multas por retraso;
consultar reportes; y preguntarle a un asistente de IA por el catálogo. Los socios pueden buscar libros en un
catálogo público sin iniciar sesión.

## 2. Tecnologías
| Parte | Herramienta |
|---|---|
| Framework web | Flask + Flask AppBuilder 5.3.0 |
| Base de datos | MySQL (XAMPP) con SQLAlchemy y PyMySQL |
| IA | Groq (modelo `openai/gpt-oss-20b`) usando el paquete `openai` |
| Gráficos | Chart.js (archivo local, funciona sin internet) |
| Control de versiones | Git y GitHub (https://github.com/Rusberth/biblioteca) |

## 3. Modelo de datos (6 tablas relacionadas)
Diagrama: `docs/DER.png` (código fuente en `docs/DER.mmd`).

| Tabla | Relaciones |
|---|---|
| `categorias` | 1 categoría tiene muchos libros |
| `autores` | 1 autor tiene muchos libros |
| `libros` | FK a `categorias` y `autores`; tiene muchos préstamos |
| `socios` | tiene muchos préstamos |
| `prestamos` | FK a `libros`, `socios` y `ab_user` (quién lo registró); tiene muchas multas |
| `multas` | FK a `prestamos` |

Restricciones: ISBN, CI y nombre de categoría únicos; ejemplares y montos no pueden ser negativos
(validados en el formulario y con `CheckConstraint` en la base de datos).

## 4. Seguridad, roles y permisos
Autenticación con usuario y contraseña (tabla `ab_user` de FAB), protección CSRF en formularios y en las
llamadas JSON, y claves guardadas en `.env` (fuera de GitHub).

| Rol | Puede |
|---|---|
| Admin | Todo, incluida la administración de usuarios y roles |
| Bibliotecario | CRUD de libros, autores, categorías, socios, préstamos y multas; mostrador; reportes; asistente |
| Consulta | Ver catálogo, autores y categorías; usar el asistente (sin datos de socios) |

Las rutas protegidas devuelven 403 si el rol no tiene el permiso. El catálogo público (`/catalogo/`) es el
único contenido abierto sin iniciar sesión.

## 5. Reglas de negocio (`app/servicios.py`)
- Un préstamo dura **14 días**.
- No se presta si no hay ejemplares disponibles, el libro está inactivo o el socio está inactivo.
- Al prestar baja en 1 el stock; al devolver sube en 1.
- Si se devuelve tarde, se crea una **multa de Bs 1 por día de retraso**.
- Una devolución no se puede registrar dos veces.
- Estas reglas se aplican igual desde el CRUD de préstamos y desde el mostrador.

## 6. Asistente de IA (`app/asistente.py`)
1. El usuario escribe una pregunta en el chat.
2. El servidor busca en la base los libros relacionados (por título, autor o categoría).
3. Si el usuario tiene permiso para ver socios y escribe un CI, agrega sus préstamos y multas.
4. Esos datos reales se envían a Groq dentro del *prompt* de sistema, con la regla de responder solo con ellos.
5. La respuesta vuelve al navegador y se muestra en el chat.

Controles: historial limitado a 10 mensajes, pregunta de máximo 500 caracteres, mensajes claros si falta la
clave o la IA no responde, y la clave solo existe en `.env`.

## 7. Reportes (`app/reportes.py`)
| Reporte | Consulta | Filtros |
|---|---|---|
| Libros más prestados | `JOIN` de libros, préstamos, autores y categorías con `COUNT` y `GROUP BY` | fechas, categoría |
| Préstamos vencidos | préstamos activos con fecha límite anterior a hoy, con días de retraso y multa estimada | socio, mínimo de días |
| Multas por socio | `SUM` con `CASE` para separar pagado y pendiente | estado, fechas |

Cada reporte se exporta a **CSV** y se imprime o guarda como **PDF** desde el navegador.

## 8. Otras funciones
Panel de inicio con indicadores y gráficos, mostrador de préstamos por CI, catálogo público con filtros y
detalle del libro, carnet de socio imprimible, cobro de multas con un clic.

## 9. Estructura del proyecto
```
app/
  __init__.py     fábrica de la aplicación
  models.py       las 6 tablas
  views.py        CRUD, menú y permisos
  servicios.py    reglas de préstamo, devolución y multas
  asistente.py    asistente de IA
  reportes.py     los 3 reportes
  dashboard.py    panel de inicio
  catalogo.py     catálogo público
  mostrador.py    mostrador y carnet
  templates/      pantallas HTML
  static/         estilos, fuentes y gráficos
config.py   init_db.py   init_roles.py   datos_prueba.py   run.py
```

## 10. Cómo ejecutarlo
Ver `README.md`. En resumen: crear la base `biblioteca_db`, `python init_db.py`, crear el administrador,
`python init_roles.py`, `python datos_prueba.py` (opcional) y `python run.py`.

## 11. Trabajo con Git
Cada funcionalidad se desarrolló en su propia rama y se integró con un Pull Request a `main`.

| Rama | Contenido |
|---|---|
| `main` | estructura base del proyecto |
| `feature/modelos` | las 6 tablas |
| `feature/crud-permisos` | vistas, menú, roles y lógica de préstamos |
| `feature/asistente-ia` | asistente con Groq |
| `feature/reportes` | los 3 reportes |
| `feature/interfaz` | rediseño, mostrador, catálogo público y datos de prueba |
| `docs/evidencias` | documentación, diagrama y capturas |

## 12. Limitaciones y mejoras posibles
- No hay migraciones de base de datos (por ejemplo con Alembic); los cambios de tablas se hacen recreando.
- Falta un sistema de reservas y renovaciones de préstamos.
- Faltan avisos automáticos por correo de préstamos por vencer.
- Para publicarlo en internet habría que usar un servidor de producción y variables de entorno seguras.
