from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class Veterinario(Base):
    __tablename__ = "veterinario"

    id_veterinario: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_usuario: Mapped[int] = mapped_column(ForeignKey("usuario.id_usuario"))
    especialidad: Mapped[str | None] = mapped_column(String(100))
    registro_profesional: Mapped[str | None] = mapped_column(String(30))

    usuario = relationship("Usuario")
