from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class Mascota(Base):
    __tablename__ = "mascota"

    id_mascota: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_propietario: Mapped[int] = mapped_column(ForeignKey("propietario.id_propietario"))
    nombre: Mapped[str] = mapped_column(String(100))
    especie: Mapped[str] = mapped_column(String(50))
    raza: Mapped[str | None] = mapped_column(String(50))
    sexo: Mapped[str] = mapped_column(String(10))
    fecha_nacimiento: Mapped[date | None] = mapped_column(Date)

    propietario = relationship("Propietario", back_populates="mascotas")
