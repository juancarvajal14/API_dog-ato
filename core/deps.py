from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from services import auth_service

_esquema = HTTPBearer(auto_error=False)


def get_sesion(credenciales: HTTPAuthorizationCredentials | None = Depends(_esquema)) -> dict:
    """Devuelve la sesión del token Bearer (guardada en Redis) o responde 401."""
    if credenciales is None:
        raise HTTPException(status_code=401, detail="No autenticado", headers={"WWW-Authenticate": "Bearer"})
    sesion = auth_service.obtener_sesion(credenciales.credentials)
    if sesion is None:
        raise HTTPException(
            status_code=401, detail="Sesión inválida o vencida", headers={"WWW-Authenticate": "Bearer"}
        )
    sesion["token"] = credenciales.credentials
    return sesion


def require_permiso(codigo_modulo: str, permiso: str):
    """Dependencia para proteger endpoints: require_permiso("CLI_CITAS", "CREAR")."""
    permiso = permiso.upper()

    def verificar(sesion: dict = Depends(get_sesion)) -> dict:
        if permiso not in sesion["permisos"].get(codigo_modulo, []):
            raise HTTPException(status_code=403, detail="No tienes permiso para realizar esta acción")
        return sesion

    return verificar


def require_algun_permiso(*requisitos: tuple[str, str]):
    """Permite el acceso si la sesión cumple AL MENOS UNO de los pares (módulo, permiso).
    Útil para listas de apoyo que alimentan formularios de varios módulos."""
    requisitos = [(codigo, permiso.upper()) for codigo, permiso in requisitos]

    def verificar(sesion: dict = Depends(get_sesion)) -> dict:
        if not any(permiso in sesion["permisos"].get(codigo, []) for codigo, permiso in requisitos):
            raise HTTPException(status_code=403, detail="No tienes permiso para realizar esta acción")
        return sesion

    return verificar
