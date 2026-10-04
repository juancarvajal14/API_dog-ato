from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class OpcionMenu(BaseModel):
    id_modulo: int
    codigo: str
    nombre: str
    ruta: str | None = None
    icono: str | None = None
    orden: int
    permisos: list[str] = []
    hijos: list["OpcionMenu"] = []


class UsuarioSesion(BaseModel):
    id_usuario: int
    nombres: str
    apellidos: str
    email: str
    roles: list[str]
    perfiles: list[str]


class SesionOut(BaseModel):
    usuario: UsuarioSesion
    menu: list[OpcionMenu]
    permisos: dict[str, list[str]]


class LoginOut(SesionOut):
    access_token: str
    token_type: str = "bearer"
    expira_en: int
    # De dónde salieron las credenciales validadas: "redis" (caché) o "postgres" (primer login / caché vencida)
    origen_credenciales: Literal["redis", "postgres"]
