from pydantic import BaseModel, EmailStr, Field

from schemas.comun import Entrada


class PropietarioIn(Entrada):
    id_tipo_documento: int
    documento: str = Field(min_length=3, max_length=20)
    nombre: str = Field(max_length=100)
    apellido: str = Field(max_length=100)
    telefono: str | None = Field(default=None, max_length=20)
    email: EmailStr | None = None
    direccion: str | None = Field(default=None, max_length=200)


class MascotaResumen(BaseModel):
    id: int
    nombre: str
    especie: str


class PropietarioOut(BaseModel):
    id: int
    id_tipo_documento: int
    tipo_documento: str
    documento: str
    nombre: str
    apellido: str
    telefono: str | None
    email: str | None
    direccion: str | None
    mascotas: list[MascotaResumen]
