"""Reglas de negocio de la biblioteca, compartidas por el CRUD y el mostrador.

Así el préstamo y la devolución se comportan igual desde cualquier pantalla.
"""
from datetime import date, datetime, timedelta
from decimal import Decimal

from .extensions import db
from .models import Multa

DIAS_PRESTAMO = 14                # plazo normal de un préstamo
MULTA_POR_DIA = Decimal("1.00")   # Bs por día de retraso


def preparar_prestamo(prestamo, usuario_id):
    """Valida y completa un préstamo nuevo (fechas, estado, stock). Lanza ValueError si no se puede."""
    libro, socio = prestamo.libro, prestamo.socio
    if libro is None or socio is None:
        raise ValueError("Elige un libro y un socio")
    if not libro.activo or libro.ejemplares_disponibles <= 0:
        raise ValueError("No hay ejemplares disponibles de este libro")
    if not socio.activo:
        raise ValueError("El socio está inactivo")
    prestamo.fecha_prestamo = date.today()
    prestamo.fecha_limite = prestamo.fecha_prestamo + timedelta(days=DIAS_PRESTAMO)
    prestamo.estado = "Activo"
    prestamo.usuario_id = usuario_id
    libro.ejemplares_disponibles -= 1
    return prestamo


def devolver_prestamo(prestamo):
    """Marca el préstamo como devuelto, repone el ejemplar y crea multa si hay retraso.

    Devuelve (dias_de_retraso, multa_o_None). Lanza ValueError si ya estaba devuelto.
    No hace commit: lo hace quien llama.
    """
    if prestamo.estado == "Devuelto":
        raise ValueError(f"El préstamo #{prestamo.id} ya fue devuelto")
    hoy = date.today()
    prestamo.fecha_devolucion = hoy
    prestamo.estado = "Devuelto"
    prestamo.libro.ejemplares_disponibles += 1
    retraso = (hoy - prestamo.fecha_limite).days
    multa = None
    if retraso > 0:
        multa = Multa(prestamo=prestamo, monto=MULTA_POR_DIA * retraso,
                      motivo=f"Retraso de {retraso} día(s)", pagada=False, fecha=datetime.now())
        db.session.add(multa)
    return max(retraso, 0), multa
