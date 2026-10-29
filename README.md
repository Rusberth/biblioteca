# Biblioteca – Flask AppBuilder + MySQL

Sistema de gestión de biblioteca (examen individual, Taller de aplicaciones en Internet, UAB).
Flask AppBuilder + MySQL (XAMPP) + asistente de IA (Groq) + reportes + interfaz propia.

## Qué incluye
- **6 tablas relacionadas** (categorías, autores, libros, socios, préstamos, multas) con CRUD, login, roles y permisos.
- **Roles**: Admin (todo), Bibliotecario (gestión completa), Consulta (solo catálogo).
- **Panel de inicio** con indicadores, gráficos y alertas de préstamos vencidos.
- **Mostrador**: prestar y devolver por CI del socio en una sola pantalla.
- **Catálogo público** (`/catalogo/`) sin necesidad de iniciar sesión.
- **Asistente de IA** (Groq) que responde con datos reales de la base.
- **3 reportes** con filtros, exportación a CSV e impresión/PDF.
- Extras: carnet de socio imprimible, cobro de multas con un clic, multa automática (Bs 1 por día de retraso).

## Puesta en marcha (Windows, Command Prompt)
1. Iniciar Apache y MySQL en XAMPP y crear la base vacía `biblioteca_db` en phpMyAdmin.
2. `py -3.14 -m venv venv` y `venv\Scripts\activate.bat`
3. `python -m pip install -r requirements.txt`
4. Copiar `.env.example` como `.env` y completar los valores (clave de Groq en `AI_API_KEY`).
5. `python init_db.py`
6. `flask --app run.py fab create-admin`
7. `python init_roles.py`
8. `python datos_prueba.py` (opcional: libros, socios, préstamos y multas de ejemplo)
9. `python run.py` y abrir http://127.0.0.1:5000

Usuarios que crea `datos_prueba.py` (solo para pruebas locales):
`bibliotecaria / Biblio123*` (Bibliotecario) y `lector / Lector123*` (Consulta).

## Documentación
- `docs/DOCUMENTACION.md`: descripción completa del sistema.
- `docs/DER.png`: diagrama entidad-relación.
- `docs/PRUEBAS.md`: lista de pruebas manuales.
- `evidencias/`: capturas de pantalla.

## Ramas
`main`, `feature/modelos`, `feature/crud-permisos`, `feature/asistente-ia`, `feature/reportes`,
`feature/interfaz`, `docs/evidencias`
