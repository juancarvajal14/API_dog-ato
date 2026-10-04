from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class TipoDocumento(Base):
    __tablename__ = "tipo_documento"

    id_tipo_documento: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(50))
    abreviacion: Mapped[str] = mapped_column(String(5))


class EstadoCita(Base):
    __tablename__ = "estado_cita"

    id_estado_cita: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(30))
