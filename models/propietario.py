from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class Propietario(Base):
    __tablename__ = "propietario"

    id_propietario: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_tipo_documento: Mapped[int] = mapped_column(ForeignKey("tipo_documento.id_tipo_documento"))
    documento: Mapped[str] = mapped_column(String(20))
    nombres: Mapped[str] = mapped_column(String(100))
    apellidos: Mapped[str] = mapped_column(String(100))
    telefono: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(100))
    direccion: Mapped[str | None] = mapped_column(String(200))
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    tipo_documento = relationship("TipoDocumento")
    mascotas = relationship("Mascota", back_populates="propietario", order_by="Mascota.nombre")
