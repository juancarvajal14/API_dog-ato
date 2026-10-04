from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import require_permiso
from schemas.veterinario import EstadoIn, VeterinarioIn, VeterinarioOut
from services import veterinario_service as servicio

router = APIRouter(prefix="/veterinarios", tags=["Veterinarios"])

MODULO = "SEG_VETERINARIOS"


@router.get("", response_model=list[VeterinarioOut], dependencies=[Depends(require_permiso(MODULO, "LEER"))])
def listar(db: Session = Depends(get_db)):
    return servicio.listar(db)


@router.get("/{id_veterinario}", response_model=VeterinarioOut, dependencies=[Depends(require_permiso(MODULO, "LEER"))])
def obtener(id_veterinario: int, db: Session = Depends(get_db)):
    return servicio.obtener(db, id_veterinario)


@router.post("", response_model=VeterinarioOut, status_code=201, dependencies=[Depends(require_permiso(MODULO, "CREAR"))])
def crear(datos: VeterinarioIn, db: Session = Depends(get_db)):
    return servicio.crear(db, datos)


# No se elimina: se activa/desactiva (los veterinarios conservan sus citas e historiales).
@router.patch("/{id_veterinario}/estado", response_model=VeterinarioOut)
def cambiar_estado(
    id_veterinario: int,
    datos: EstadoIn,
    db: Session = Depends(get_db),
    sesion: dict = Depends(require_permiso(MODULO, "ACTUALIZAR")),
):
    return servicio.cambiar_estado(db, id_veterinario, datos.activo, sesion["usuario"]["id_usuario"])
