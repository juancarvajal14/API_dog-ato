import secrets

import bcrypt

# bcrypt solo considera los primeros 72 bytes de la contraseña.
_MAX_BYTES = 72


def _a_bytes(texto: str) -> bytes:
    return texto.encode("utf-8")[:_MAX_BYTES]


def hashear_contrasena(contrasena: str) -> str:
    return bcrypt.hashpw(_a_bytes(contrasena), bcrypt.gensalt(rounds=10)).decode()


def verificar_contrasena(contrasena: str, hash_guardado: str) -> bool:
    try:
        return bcrypt.checkpw(_a_bytes(contrasena), hash_guardado.encode())
    except ValueError:
        return False


# Hash de relleno: se verifica cuando el correo no existe para que la respuesta
# tarde lo mismo y no se pueda deducir qué correos están registrados.
HASH_RELLENO = hashear_contrasena("relleno-no-valido")


def generar_token() -> str:
    return secrets.token_urlsafe(32)
