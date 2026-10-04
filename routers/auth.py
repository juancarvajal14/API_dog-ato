from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import get_sesion
from schemas.auth import LoginIn, LoginOut, SesionOut
from services import auth_service

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/login", response_model=LoginOut)
def login(datos: LoginIn, db: Session = Depends(get_db)):
    return auth_service.iniciar_sesion(db, datos.email, datos.password)


@router.get("/me", response_model=SesionOut)
def me(sesion: dict = Depends(get_sesion)):
    return sesion


@router.post("/logout", status_code=204)
def logout(sesion: dict = Depends(get_sesion)):
    auth_service.cerrar_sesion(sesion["token"], sesion["usuario"]["id_usuario"])
