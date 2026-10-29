"""Modelos de la biblioteca: 6 tablas relacionadas.

categorias 1──N libros N──1 autores
socios 1──N prestamos N──1 libros
prestamos 1──N multas
prestamos N──1 ab_user (bibliotecario que registró el préstamo)
"""
from datetime import date, datetime

from flask_appbuilder import Model
from flask_appbuilder.security.sqla.models import User
from sqlalchemy import (
    Boolean, CheckConstraint, Column, Date, DateTime, ForeignKey,
    Integer, Numeric, String,
)
from sqlalchemy.orm import relationship


class Categoria(Model):
    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), unique=True, nullable=False)
    descripcion = Column(String(250), nullable=True)

    libros = relationship("Libro", back_populates="categoria")

    def __repr__(self):
        return self.nombre


class Autor(Model):
    __tablename__ = "autores"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(120), nullable=False)
    nacionalidad = Column(String(80), nullable=True)

    libros = relationship("Libro", back_populates="autor")

    def __repr__(self):
        return self.nombre


class Libro(Model):
    __tablename__ = "libros"
    __table_args__ = (
        CheckConstraint("ejemplares_total >= 0", name="ck_libro_total"),
        CheckConstraint("ejemplares_disponibles >= 0", name="ck_libro_disp"),
    )

    id = Column(Integer, primary_key=True)
    titulo = Column(String(200), nullable=False)
    isbn = Column(String(20), unique=True, nullable=False)
    anio_publicacion = Column(Integer, nullable=True)
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=False)
    autor_id = Column(Integer, ForeignKey("autores.id"), nullable=False)
    ejemplares_total = Column(Integer, nullable=False, default=1)
    ejemplares_disponibles = Column(Integer, nullable=False, default=1)
    activo = Column(Boolean, default=True)

    categoria = relationship("Categoria", back_populates="libros")
    autor = relationship("Autor", back_populates="libros")
    prestamos = relationship("Prestamo", back_populates="libro")

    @property
    def disponibilidad(self):
        return "Disponible" if self.ejemplares_disponibles > 0 else "Agotado"

    def __repr__(self):
        return self.titulo


class Socio(Model):
    __tablename__ = "socios"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(120), nullable=False)
    ci = Column(String(20), unique=True, nullable=False)
    email = Column(String(120), nullable=True)
    telefono = Column(String(30), nullable=True)
    fecha_registro = Column(Date, default=date.today, nullable=False)
    activo = Column(Boolean, default=True)

    prestamos = relationship("Prestamo", back_populates="socio")

    def __repr__(self):
        return self.nombre


class Prestamo(Model):
    __tablename__ = "prestamos"

    id = Column(Integer, primary_key=True)
    libro_id = Column(Integer, ForeignKey("libros.id"), nullable=False)
    socio_id = Column(Integer, ForeignKey("socios.id"), nullable=False)
    usuario_id = Column(Integer, ForeignKey("ab_user.id"), nullable=True)
    fecha_prestamo = Column(Date, default=date.today, nullable=False)
    fecha_limite = Column(Date, nullable=False)
    fecha_devolucion = Column(Date, nullable=True)
    estado = Column(String(20), default="Activo", nullable=False)  # Activo / Devuelto

    libro = relationship("Libro", back_populates="prestamos")
    socio = relationship("Socio", back_populates="prestamos")
    usuario = relationship(User)
    multas = relationship("Multa", back_populates="prestamo")

    @property
    def vencido(self):
        return self.fecha_devolucion is None and self.fecha_limite < date.today()

    def __repr__(self):
        return f"Préstamo #{self.id}"


class Multa(Model):
    __tablename__ = "multas"
    __table_args__ = (CheckConstraint("monto >= 0", name="ck_multa_monto"),)

    id = Column(Integer, primary_key=True)
    prestamo_id = Column(Integer, ForeignKey("prestamos.id"), nullable=False)
    monto = Column(Numeric(10, 2), nullable=False)
    motivo = Column(String(250), nullable=True)
    pagada = Column(Boolean, default=False)
    fecha = Column(DateTime, default=datetime.now, nullable=False)

    prestamo = relationship("Prestamo", back_populates="multas")

    def __repr__(self):
        return f"Multa #{self.id}"