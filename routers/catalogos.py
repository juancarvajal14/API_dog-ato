"""Listas de apoyo para los formularios. Devuelven solo los campos mínimos y exigen
el permiso del formulario que las usa (no el de leer el módulo completo)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import get_sesion, require_algun_permiso, require_permiso
from schemas.catalogos import PerfilOut, PropietarioCatalogo, TipoDocumentoOut
from schemas.comun import PersonaResumen
from services import catalogo_service as servicio

router = APIRouter(prefix="/catalogos", tags=["Catálogos"])


@router.get("/tipos-documento", response_model=list[TipoDocumentoOut], dependencies=[Depends(get_sesion)])
def tipos_documento(db: Session = Depends(get_db)):
    return servicio.tipos_documento(db)


@router.get(
    "/propietarios",
    response_model=list[PropietarioCatalogo],
    dependencies=[Depends(require_algun_permiso(("CLI_MASCOTAS", "CREAR"), ("CLI_CITAS", "CREAR")))],
)
def propietarios(db: Session = Depends(get_db)):
    return servicio.propietarios_con_mascotas(db)


@router.get(
    "/veterinarios",
    response_model=list[PersonaResumen],
    dependencies=[Depends(require_permiso("CLI_CITAS", "CREAR"))],
)
def veterinarios(db: Session = Depends(get_db)):
    return servicio.veterinarios_activos(db)


@router.get(
    "/perfiles-veterinario",
    response_model=list[PerfilOut],
    dependencies=[Depends(require_permiso("SEG_VETERINARIOS", "CREAR"))],
)
def perfiles_veterinario(db: Session = Depends(get_db)):
    return servicio.perfiles_de_veterinario(db)
