from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from schemas.comun import Entrada, PersonaResumen


class MascotaIn(Entrada):
    nombre: str = Field(max_length=100)
    especie: str = Field(max_length=50)
    raza: str | None = Field(default=None, max_length=50)
    sexo: Literal["macho", "hembra"]
    fecha_nacimiento: date | None = None
    propietario_id: int


class PropietarioDeMascota(PersonaResumen):
    telefono: str | None


class MascotaOut(BaseModel):
    id: int
    nombre: str
    especie: str
    raza: str | None
    sexo: str
    fecha_nacimiento: date | None
    propietario_id: int
    propietario: PropietarioDeMascota
