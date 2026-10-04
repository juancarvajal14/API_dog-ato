from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import require_permiso
from schemas.seguridad import EstadoIn, ModuloActualizar, ModuloCrear, ModuloOut, PermisoOut
from services import seguridad_service as servicio

router = APIRouter(prefix="/modulos", tags=["Módulos y permisos"])

MODULO = "SEG_MODULOS"


@router.get("", response_model=list[ModuloOut], dependencies=[Depends(require_permiso(MODULO, "LEER"))])
def listar(db: Session = Depends(get_db)):
    return servicio.listar_modulos(db)


@router.get("/permisos", response_model=list[PermisoOut], dependencies=[Depends(require_permiso(MODULO, "LEER"))])
def permisos(db: Session = Depends(get_db)):
    return servicio.listar_permisos(db)


@router.post("", response_model=ModuloOut, status_code=201)
def crear(datos: ModuloCrear, db: Session = Depends(get_db), sesion: dict = Depends(require_permiso(MODULO, "CREAR"))):
    return servicio.crear_modulo(db, sesion, datos)


@router.put("/{id_modulo}", response_model=ModuloOut)
def actualizar(id_modulo: int, datos: ModuloActualizar, db: Session = Depends(get_db), sesion: dict = Depends(require_permiso(MODULO, "ACTUALIZAR"))):
    return servicio.actualizar_modulo(db, sesion, id_modulo, datos)


@router.patch("/{id_modulo}/estado", response_model=ModuloOut)
def cambiar_estado(id_modulo: int, datos: EstadoIn, db: Session = Depends(get_db), sesion: dict = Depends(require_permiso(MODULO, "ACTUALIZAR"))):
    return servicio.cambiar_estado_modulo(db, sesion, id_modulo, datos.activo)
