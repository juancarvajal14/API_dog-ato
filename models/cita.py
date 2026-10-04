from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class Cita(Base):
    __tablename__ = "cita"

    id_cita: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_mascota: Mapped[int] = mapped_column(ForeignKey("mascota.id_mascota"))
    id_veterinario: Mapped[int] = mapped_column(ForeignKey("veterinario.id_veterinario"))
    id_estado_cita: Mapped[int] = mapped_column(ForeignKey("estado_cita.id_estado_cita"))
    fecha_hora: Mapped[datetime] = mapped_column(DateTime)
    motivo_consulta: Mapped[str] = mapped_column(Text)

    mascota = relationship("Mascota")
    veterinario = relationship("Veterinario")
    estado = relationship("EstadoCita")


class HistorialClinico(Base):
    __tablename__ = "historial_clinico"

    id_historial_clinico: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_cita: Mapped[int] = mapped_column(ForeignKey("cita.id_cita"))
    fecha_registro: Mapped[datetime] = mapped_column(DateTime)
    diagnostico: Mapped[str | None] = mapped_column(Text)
    tratamiento: Mapped[str | None] = mapped_column(Text)
    observaciones: Mapped[str | None] = mapped_column(Text)

    cita = relationship("Cita")
