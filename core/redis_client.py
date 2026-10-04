import redis

from core.config import settings

PREFIJO = "dogato:"

# Timeouts cortos: si Redis cae, el API responde rápido en vez de quedarse colgado.
cliente = redis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    username=settings.redis_user,
    password=settings.redis_password,
    ssl=settings.redis_ssl,
    decode_responses=True,
    socket_connect_timeout=2,
    socket_timeout=2,
)


def clave_sesion(token: str) -> str:
    return f"{PREFIJO}sesion:{token}"


def clave_sesiones_usuario(id_usuario: int) -> str:
    return f"{PREFIJO}usuario_sesiones:{id_usuario}"


def clave_credenciales(email: str) -> str:
    return f"{PREFIJO}cred:{email}"


def clave_intentos(email: str) -> str:
    return f"{PREFIJO}intentos:{email}"


def redis_disponible() -> bool:
    try:
        return bool(cliente.ping())
    except redis.RedisError:
        return False
