# Biblioteca – Flask AppBuilder + MySQL

Sistema de biblioteca (examen individual, Taller de aplicaciones en Internet, UAB).
Flask AppBuilder + MySQL (XAMPP) + asistente de IA (Groq) + reportes.

## Puesta en marcha (Windows, Command Prompt)
1. Iniciar Apache y MySQL en XAMPP y crear la base vacía `biblioteca_db` en phpMyAdmin.
2. `py -3.14 -m venv venv` y `venv\Scripts\activate.bat`
3. `python -m pip install -r requirements.txt`
4. Copiar `.env.example` como `.env` y completar los valores.
5. `python init_db.py`
6. `flask --app run.py fab create-admin`
7. `python run.py` y abrir http://127.0.0.1:5000

## Ramas
- `main`: estructura base
- `feature/modelos`, `feature/crud-permisos`, `feature/asistente-ia`, `feature/reportes`, `docs/evidencias`
