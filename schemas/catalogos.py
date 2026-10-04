from pydantic import BaseModel

from schemas.comun import PersonaResumen
from schemas.propietario import MascotaResumen


class TipoDocumentoOut(BaseModel):
    id: int
    nombre: str
    abreviacion: str


class PerfilOut(BaseModel):
    id: int
    nombre: str
    descripcion: str | None


class PropietarioCatalogo(PersonaResumen):
    documento: str
    mascotas: list[MascotaResumen]
