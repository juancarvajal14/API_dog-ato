"""Genera db/DOG-ATO_produccion.sql a partir del script de desarrollo (DDL.sql).

El script de producción:
  * NO borra ni crea la base de datos (se crea en el proveedor y se conecta directamente a ella);
  * NO carga datos de demostración;
  * recibe el correo y la contraseña del administrador inicial por variables de psql
    (-v admin_email=... -v admin_password=...), en vez de usar una contraseña conocida.

Así la estructura, las funciones, los triggers y la seguridad salen de UN solo archivo fuente.
Uso:  python db/generar_produccion.py
"""
import re
from pathlib import Path

BASE = Path(__file__).parent
ORIGEN = BASE / "DDL.sql"
DESTINO = BASE / "DOG-ATO_produccion.sql"

CABECERA = """-- =====================================================================
-- DOG-ATO · PostgreSQL · PRODUCCIÓN
-- ARCHIVO GENERADO por db/generar_produccion.py a partir de DDL.sql: no editar a mano.
--
-- No crea ni borra la base de datos (créala en tu proveedor y conéctate a ella) y no carga datos de demo.
-- Uso:
--   psql "<cadena de conexión>" -v admin_email='correo@dominio.com' -v admin_password='<clave larga>' \\
--        -f DOG-ATO_produccion.sql
-- Requiere PostgreSQL 13+ y permiso para CREATE EXTENSION pgcrypto.
-- =====================================================================

\\set ON_ERROR_STOP on
\\encoding UTF8

\\if :{?admin_email}
\\else
  \\echo 'Falta -v admin_email=...'
  \\quit
\\endif
\\if :{?admin_password}
\\else
  \\echo 'Falta -v admin_password=...'
  \\quit
\\endif

"""


def generar() -> str:
    texto = ORIGEN.read_text(encoding="utf8")

    # 1) Quitar la cabecera de desarrollo (hasta el primer BEGIN;)
    inicio = texto.index("\nBEGIN;")
    texto = texto[inicio + 1 :]

    # 2) Quitar los datos de demostración (hasta el COMMIT final)
    marca = texto.index("-- ---------------------------------------------------------------------\n-- DATOS DE DEMOSTRACIÓN")
    texto = texto[:marca] + "COMMIT;\n"

    # 3) Administrador inicial desde variables, sin contraseña conocida
    texto = re.sub(
        r"-- Administrador inicial.*\n-- \(cámbiala.*\n",
        "-- Administrador inicial: correo y contraseña llegan por las variables admin_email / admin_password.\n",
        texto,
    )
    texto = texto.replace("'admin@veterinaria.com'", ":'admin_email'")
    texto = texto.replace("crypt('Admin12345*', gen_salt('bf', 10))", "crypt(:'admin_password', gen_salt('bf', 10))")

    texto = texto.replace("'3105324587'", "NULL")  # teléfono de ejemplo del administrador de desarrollo
    assert "3105324587" not in texto and "Admin12345" not in texto and "admin@veterinaria" not in texto, "quedó una credencial de desarrollo"
    assert "DATOS DE DEMOSTRACIÓN" not in texto and "dogato.com" not in texto, "quedaron datos de demo"
    return CABECERA + texto


if __name__ == "__main__":
    DESTINO.write_text(generar(), encoding="utf8", newline="\n")
    print(f"Generado {DESTINO}")
