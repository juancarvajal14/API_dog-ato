from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import require_algun_permiso, require_permiso
from schemas.seguridad import EstadoIn, RolIn, RolOut
from services import seguridad_service as servicio

router = APIRouter(prefix="/roles", tags=["Roles"])

MODULO = "SEG_ROLES"


# La lista de roles también alimenta el formulario de Perfiles.
@router.get(
    "",
    response_model=list[RolOut],
    dependencies=[Depends(require_algun_permiso((MODULO, "LEER"), ("SEG_PERFILES", "LEER")))],
)
def listar(db: Session = Depends(get_db)):
    return servicio.listar_roles(db)


@router.post("", response_model=RolOut, status_code=201, dependencies=[Depends(require_permiso(MODULO, "CREAR"))])
def crear(datos: RolIn, db: Session = Depends(get_db)):
    return servicio.crear_rol(db, datos)


@router.put("/{id_rol}", response_model=RolOut)
def actualizar(id_rol: int, datos: RolIn, db: Session = Depends(get_db), sesion: dict = Depends(require_permiso(MODULO, "ACTUALIZAR"))):
    return servicio.actualizar_rol(db, sesion, id_rol, datos)


# No se elimina: se activa/desactiva.
@router.patch("/{id_rol}/estado", response_model=RolOut)
def cambiar_estado(id_rol: int, datos: EstadoIn, db: Session = Depends(get_db), sesion: dict = Depends(require_permiso(MODULO, "ACTUALIZAR"))):
    return servicio.cambiar_estado_rol(db, sesion, id_rol, datos.activo)
