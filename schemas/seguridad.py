from typing import Literal

from pydantic import BaseModel, Field

from schemas.comun import Entrada

NombrePermiso = Literal["CREAR", "LEER", "ACTUALIZAR", "ELIMINAR"]


class EstadoIn(BaseModel):
    activo: bool


# ---------- roles ----------
class RolIn(Entrada):
    nombre: str = Field(max_length=50)


class RolOut(BaseModel):
    id: int
    nombre: str
    activo: bool
    es_sistema: bool
    total_perfiles: int


# ---------- perfiles ----------
class PerfilIn(Entrada):
    id_rol: int
    nombre: str = Field(max_length=50)
    descripcion: str | None = Field(default=None, max_length=500)


class PerfilOut(BaseModel):
    id: int
    id_rol: int
    rol: str
    nombre: str
    descripcion: str | None
    activo: bool
    total_usuarios: int


# ---------- módulos ----------
class ModuloBase(Entrada):
    id_modulo_padre: int | None = None
    nombre: str = Field(max_length=50)
    descripcion: str | None = Field(default=None, max_length=500)
    ruta: str | None = Field(default=None, max_length=200, pattern=r"^/[a-z0-9/_-]*$")
    icono: str | None = Field(default=None, max_length=40)
    orden: int = Field(default=1, ge=1, le=999)


class ModuloCrear(ModuloBase):
    codigo: str = Field(min_length=3, max_length=40, pattern=r"^[A-Z][A-Z0-9_]*$")


class ModuloActualizar(ModuloBase):
    pass


class ModuloOut(BaseModel):
    id: int
    id_modulo_padre: int | None
    padre: str | None
    codigo: str
    nombre: str
    descripcion: str | None
    ruta: str | None
    icono: str | None
    orden: int
    activo: bool
    tipo: Literal["carpeta", "opcion"]
    es_sistema: bool


# ---------- matriz de permisos ----------
class PermisoOut(BaseModel):
    id: int
    nombre: str
    descripcion: str | None


class FilaMatriz(BaseModel):
    codigo: str
    nombre: str
    carpeta: str | None
    activo: bool
    permisos: list[str]


class MatrizOut(BaseModel):
    id_perfil: int
    perfil: str
    permisos_disponibles: list[str]
    modulos: list[FilaMatriz]


class MatrizIn(BaseModel):
    # { "CLI_CITAS": ["CREAR", "LEER"], ... }; los módulos que no aparezcan quedan sin permisos
    asignaciones: dict[str, list[NombrePermiso]]
