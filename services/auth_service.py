import json
import time

import redis
from sqlalchemy.orm import Session

from core import redis_client as rc
from core.config import settings
from core.errors import ErrorNegocio
from core.redis_client import cliente
from core.security import HASH_RELLENO, generar_token, verificar_contrasena
from repositories import auth_repository as repo

CREDENCIALES_INVALIDAS = "Correo o contraseña incorrectos"
SIN_SESIONES = "El servicio de sesiones no está disponible. Intenta más tarde"


def _armar_arbol(filas: list[dict]) -> list[dict]:
    """Convierte las filas planas de fn_menu_usuario en carpetas con sus opciones."""
    nodos = {
        f["id_modulo"]: {
            "id_modulo": f["id_modulo"],
            "codigo": f["codigo"],
            "nombre": f["nombre"],
            "ruta": f["ruta"],
            "icono": f["icono"],
            "orden": f["orden"],
            "permisos": list(f["permisos"]),
            "hijos": [],
        }
        for f in filas
    }
    raiz = []
    for f in filas:
        nodo = nodos[f["id_modulo"]]
        padre = nodos.get(f["id_modulo_padre"]) if f["id_modulo_padre"] else None
        (padre["hijos"] if padre else raiz).append(nodo)
    for nodo in nodos.values():
        nodo["hijos"].sort(key=lambda n: n["orden"])
    raiz.sort(key=lambda n: n["orden"])
    return raiz


# ---------- caché de credenciales, intentos y sesión (Redis) ----------

def _credenciales_de_cache(email: str) -> dict | None:
    try:
        datos = cliente.hgetall(rc.clave_credenciales(email))
    except redis.RedisError:
        return None
    if not datos:
        return None
    datos["id_usuario"] = int(datos["id_usuario"])
    datos["activo"] = datos["activo"] == "1"
    datos["contrasena_hash"] = datos.pop("hash")
    return datos


def _guardar_credenciales(usuario: dict) -> None:
    clave = rc.clave_credenciales(usuario["email"].lower())
    try:
        cliente.hset(
            clave,
            mapping={
                "id_usuario": usuario["id_usuario"],
                "nombres": usuario["nombres"],
                "apellidos": usuario["apellidos"],
                "email": usuario["email"],
                "hash": usuario["contrasena_hash"],
                "activo": "1" if usuario["activo"] else "0",
            },
        )
        cliente.expire(clave, settings.credenciales_ttl)
    except redis.RedisError:
        pass  # sin caché se sigue funcionando contra Postgres


def _verificar_bloqueo(email: str) -> None:
    try:
        intentos = int(cliente.get(rc.clave_intentos(email)) or 0)
        espera = max(cliente.ttl(rc.clave_intentos(email)), 1) if intentos >= settings.max_intentos_login else 0
    except redis.RedisError:
        return
    if espera:
        raise ErrorNegocio(
            429,
            f"Demasiados intentos fallidos. Intenta de nuevo en {-(-espera // 60)} minuto(s)",
            headers={"Retry-After": str(espera)},
        )


def _registrar_fallo(email: str) -> None:
    try:
        clave = rc.clave_intentos(email)
        if cliente.incr(clave) == 1:
            cliente.expire(clave, settings.bloqueo_login_ttl)
    except redis.RedisError:
        pass


def _crear_sesion(datos: dict) -> str:
    token = generar_token()
    id_usuario = datos["usuario"]["id_usuario"]
    try:
        pipe = cliente.pipeline()
        pipe.set(rc.clave_sesion(token), json.dumps(datos), ex=settings.sesion_ttl)
        pipe.sadd(rc.clave_sesiones_usuario(id_usuario), token)
        pipe.expire(rc.clave_sesiones_usuario(id_usuario), settings.sesion_ttl)
        pipe.execute()
    except redis.RedisError:
        raise ErrorNegocio(503, SIN_SESIONES)
    return token


def _construir_datos_sesion(db: Session, usuario: dict) -> dict:
    """Menú y permisos salen SIEMPRE de la BD (fn_menu_usuario / fn_permisos_usuario)."""
    id_usuario = usuario["id_usuario"]
    filas_menu = repo.menu_usuario(db, id_usuario)
    if not filas_menu:
        raise ErrorNegocio(403, "Tu usuario no tiene módulos habilitados. Contacta a un administrador")

    roles, perfiles = repo.roles_y_perfiles(db, id_usuario)
    return {
        "usuario": {
            "id_usuario": id_usuario,
            "nombres": usuario["nombres"],
            "apellidos": usuario["apellidos"],
            "email": usuario["email"],
            "roles": roles,
            "perfiles": perfiles,
        },
        "menu": _armar_arbol(filas_menu),
        "permisos": repo.permisos_por_modulo(db, id_usuario),
        "creada": int(time.time()),
    }


# ---------- casos de uso ----------

def iniciar_sesion(db: Session, email: str, contrasena: str) -> dict:
    email = email.strip().lower()
    _verificar_bloqueo(email)

    origen = "redis"
    usuario = _credenciales_de_cache(email)
    if usuario is None:
        origen = "postgres"
        usuario = repo.buscar_usuario_por_email(db, email)
    if usuario is None:
        verificar_contrasena(contrasena, HASH_RELLENO)
        _registrar_fallo(email)
        raise ErrorNegocio(401, CREDENCIALES_INVALIDAS)

    if not verificar_contrasena(contrasena, usuario["contrasena_hash"]):
        _registrar_fallo(email)
        raise ErrorNegocio(401, CREDENCIALES_INVALIDAS)

    if not usuario["activo"]:
        raise ErrorNegocio(403, "Esta cuenta está inactiva. Contacta a un administrador")

    _guardar_credenciales(usuario)

    datos = _construir_datos_sesion(db, usuario)
    token = _crear_sesion(datos)

    try:
        cliente.delete(rc.clave_intentos(email))
    except redis.RedisError:
        pass

    return {
        **datos,
        "access_token": token,
        "token_type": "bearer",
        "expira_en": settings.sesion_ttl,
        "origen_credenciales": origen,
    }


def obtener_sesion(token: str) -> dict | None:
    """Lee la sesión y renueva su vencimiento (sesión deslizante). None si no existe o venció."""
    try:
        crudo = cliente.get(rc.clave_sesion(token))
        if crudo is None:
            return None
        cliente.expire(rc.clave_sesion(token), settings.sesion_ttl)
    except redis.RedisError:
        raise ErrorNegocio(503, SIN_SESIONES)
    return json.loads(crudo)


def cerrar_sesion(token: str, id_usuario: int) -> None:
    try:
        pipe = cliente.pipeline()
        pipe.delete(rc.clave_sesion(token))
        pipe.srem(rc.clave_sesiones_usuario(id_usuario), token)
        pipe.execute()
    except redis.RedisError:
        raise ErrorNegocio(503, SIN_SESIONES)


def invalidar_usuario(id_usuario: int, email: str | None = None) -> None:
    """Cierra todas las sesiones de un usuario y descarta su caché de credenciales.
    Debe llamarse cuando cambian sus permisos, su perfil, su contraseña o su estado."""
    try:
        clave = rc.clave_sesiones_usuario(id_usuario)
        llaves = [rc.clave_sesion(t) for t in cliente.smembers(clave)] + [clave]
        if email:
            llaves.append(rc.clave_credenciales(email.strip().lower()))
        cliente.delete(*llaves)
    except redis.RedisError:
        pass


# ---------- sincronización de sesiones cuando cambia la seguridad ----------

def refrescar_sesion(db: Session, sesion: dict) -> None:
    """Recalcula menú y permisos de la sesión actual desde la BD y la reescribe en Redis (conserva el token)."""
    usuario = repo.buscar_usuario_por_email(db, sesion["usuario"]["email"])
    try:
        clave = rc.clave_sesion(sesion["token"])
        ttl = cliente.ttl(clave)
        if usuario is None or not usuario["activo"]:
            cliente.delete(clave)
            return
        datos = _construir_datos_sesion(db, usuario)
        datos["creada"] = sesion.get("creada", datos["creada"])
        cliente.set(clave, json.dumps(datos), ex=ttl if ttl > 0 else settings.sesion_ttl)
    except ErrorNegocio:
        # Se quedó sin módulos: se cierra la sesión.
        cliente.delete(rc.clave_sesion(sesion["token"]))
    except redis.RedisError:
        pass


def invalidar_usuarios(ids_usuario: list[int], conservar_token: str | None = None) -> None:
    """Cierra todas las sesiones de los usuarios indicados, salvo `conservar_token`."""
    try:
        for id_usuario in ids_usuario:
            clave = rc.clave_sesiones_usuario(id_usuario)
            tokens = [t for t in cliente.smembers(clave) if t != conservar_token]
            if tokens:
                cliente.delete(*[rc.clave_sesion(t) for t in tokens])
                cliente.srem(clave, *tokens)
    except redis.RedisError:
        pass


def invalidar_todas(conservar_token: str | None = None) -> None:
    """Cierra todas las sesiones (cambios que afectan a cualquier usuario, p. ej. el menú), salvo `conservar_token`."""
    try:
        for clave in cliente.scan_iter(f"{rc.PREFIJO}sesion:*"):
            if clave != rc.clave_sesion(conservar_token or ""):
                cliente.delete(clave)
    except redis.RedisError:
        pass
