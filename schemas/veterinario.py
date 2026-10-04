from typing import Literal

from pydantic import BaseModel, EmailStr, Field

from schemas.comun import Entrada


class VeterinarioIn(Entrada):
    id_tipo_documento: int
    documento: str = Field(min_length=3, max_length=20)
    nombre: str = Field(max_length=100)
    apellido: str = Field(max_length=100)
    telefono: str | None = Field(default=None, max_length=20)
    direccion: str | None = Field(default=None, max_length=200)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    especialidad: str | None = Field(default=None, max_length=100)
    registro_profesional: str | None = Field(default=None, max_length=30)
    id_perfil: int


class EstadoIn(BaseModel):
    activo: bool


class VeterinarioOut(BaseModel):
    id: int
    id_usuario: int
    id_tipo_documento: int
    tipo_documento: str
    documento: str
    nombre: str
    apellido: str
    telefono: str | None
    email: str
    direccion: str | None
    especialidad: str | None
    registro_profesional: str | None
    activo: bool
    rol: Literal["administrador", "veterinario"]
    perfiles: list[str]
