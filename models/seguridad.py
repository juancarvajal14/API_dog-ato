from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class Rol(Base):
    __tablename__ = "rol"

    id_rol: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(50))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)

    perfiles = relationship("Perfil", back_populates="rol")


class Perfil(Base):
    __tablename__ = "perfil"

    id_perfil: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_rol: Mapped[int] = mapped_column(ForeignKey("rol.id_rol"))
    nombre: Mapped[str] = mapped_column(String(50))
    descripcion: Mapped[str | None] = mapped_column(String(500))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)

    rol = relationship("Rol", back_populates="perfiles")


class Modulo(Base):
    __tablename__ = "modulo"

    id_modulo: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_modulo_padre: Mapped[int | None] = mapped_column(ForeignKey("modulo.id_modulo"))
    codigo: Mapped[str] = mapped_column(String(40))
    nombre: Mapped[str] = mapped_column(String(50))
    descripcion: Mapped[str | None] = mapped_column(String(500))
    ruta: Mapped[str | None] = mapped_column(String(200))
    icono: Mapped[str | None] = mapped_column(String(40))
    orden: Mapped[int] = mapped_column(Integer, default=1)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)

    padre = relationship("Modulo", remote_side=[id_modulo])


class Permiso(Base):
    __tablename__ = "permiso"

    id_permiso: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(30))
    descripcion: Mapped[str | None] = mapped_column(String(200))
