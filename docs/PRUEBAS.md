# Pruebas manuales

Usuarios: `admin` (el que creaste), `bibliotecaria / Biblio123*` y `lector / Lector123*`.
Antes de empezar: `python datos_prueba.py`. Marca cada prueba y guarda una captura en `evidencias/`.

| # | Prueba | Resultado esperado |
|---|---|---|
| 1 | Entrar con `admin` | Se ve el panel con indicadores y el menú completo |
| 2 | Entrar con una clave incorrecta | Mensaje de error, no entra |
| 3 | Catálogo → Libros → agregar un libro | Aparece en la lista |
| 4 | Agregar un libro con ejemplares negativos | El formulario lo rechaza |
| 5 | Agregar una categoría con nombre repetido | Se rechaza |
| 6 | Mostrador: buscar un socio por CI y prestar un libro | Mensaje con la fecha límite; baja el stock |
| 7 | Prestar un libro sin ejemplares | Mensaje "No hay ejemplares disponibles" |
| 8 | Devolver un préstamo vencido | Se crea una multa de Bs 1 por día de retraso |
| 9 | Multas → marcar como pagada | La multa pasa a pagada |
| 10 | Reportes: aplicar un filtro en cada uno | Cambian las filas; el CSV baja con el filtro |
| 11 | Asistente: "¿Tienen libros de ciencia?" | Responde con libros reales de la base |
| 12 | Asistente: "multas del socio <CI>" (con `bibliotecaria`) | Muestra préstamos y multas del socio |
| 13 | Asistente con `lector` y un CI | No recibe datos del socio |
| 14 | Entrar con `lector` y abrir `/mostrador/` | Error 403 (sin permiso) |
| 15 | Abrir `/catalogo/` sin iniciar sesión | Se ve el catálogo público |
| 16 | Carnet de un socio (Socios → Ver carnet) | Se abre el carnet imprimible |
