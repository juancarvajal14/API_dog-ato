"""Pruebas directas de la base de datos (funciones, triggers y restricciones).
Cada prueba corre dentro de una transacción que se revierte: no deja datos."""
import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from core.database import engine


@pytest.fixture
def conn():
    with engine.connect() as c:
        transaccion = c.begin()
        yield c
        transaccion.rollback()


def uno(conn, sql, **params):
    return conn.execute(text(sql), params).scalar()


def intentar(conn, sql, **params):
    """Ejecuta una sentencia que debe fallar y devuelve el mensaje de la BD (sin romper la transacción)."""
    punto = conn.begin_nested()
    with pytest.raises(DBAPIError) as info:
        conn.execute(text(sql), params)
    punto.rollback()
    return str(info.value.orig)


def id_admin(conn):
    return uno(conn, "SELECT id_usuario FROM usuario WHERE email = 'admin@veterinaria.com'")


def nuevo_propietario_y_mascota(conn):
    documento = "T9" + uuid.uuid4().hex[:12]  # único en cada llamada
    pid = uno(conn, "INSERT INTO propietario (id_tipo_documento, documento, nombres, apellidos) VALUES (1,:d,'A','B') RETURNING id_propietario", d=documento)
    return uno(conn, "INSERT INTO mascota (id_propietario, nombre, especie, sexo) VALUES (:p,'M','Perro','macho') RETURNING id_mascota", p=pid)


def veterinario_activo(conn):
    return uno(
        conn,
        "SELECT v.id_veterinario FROM veterinario v JOIN usuario u USING (id_usuario) WHERE u.activo ORDER BY 1 LIMIT 1",
    )


def estado(conn, nombre):
    return uno(conn, "SELECT id_estado_cita FROM estado_cita WHERE nombre = :n", n=nombre)


def nueva_cita(conn, estado_nombre="pendiente"):
    return uno(
        conn,
        "INSERT INTO cita (id_mascota, id_veterinario, id_estado_cita, fecha_hora, motivo_consulta)"
        " VALUES (:m, :v, :e, now(), 'Control') RETURNING id_cita",
        m=nuevo_propietario_y_mascota(conn), v=veterinario_activo(conn), e=estado(conn, estado_nombre),
    )


# ---------- catálogos y seed ----------

def test_catalogos_y_seed(conn):
    assert uno(conn, "SELECT count(*) FROM tipo_documento") == 4
    assert [r[0] for r in conn.execute(text("SELECT nombre FROM estado_cita ORDER BY id_estado_cita"))] == ["pendiente", "completada", "cancelada"]
    assert [r[0] for r in conn.execute(text("SELECT nombre FROM permiso ORDER BY id_permiso"))] == ["CREAR", "LEER", "ACTUALIZAR", "ELIMINAR"]
    assert uno(conn, "SELECT count(*) FROM modulo WHERE ruta IS NULL") == 2  # carpetas
    assert uno(conn, "SELECT count(*) FROM modulo WHERE ruta IS NOT NULL") == 8  # opciones


def test_contrasenas_con_hash_bcrypt(conn):
    assert uno(conn, "SELECT count(*) FROM usuario WHERE contrasena_hash NOT LIKE '$2%'") == 0


# ---------- funciones de seguridad ----------

def test_menu_y_permisos_del_administrador(conn):
    filas = conn.execute(text("SELECT codigo, permisos FROM fn_menu_usuario(:u)"), {"u": id_admin(conn)}).all()
    assert len(filas) == 10
    permisos = {codigo: set(p) for codigo, p in filas}
    assert permisos["CLI_HISTORIAL"] == {"LEER"}
    assert permisos["SEG_MODULOS"] == {"CREAR", "LEER", "ACTUALIZAR"}
    assert permisos["SEGURIDAD"] == set()  # carpeta: se muestra por tener opciones, sin permisos propios


def test_fn_tiene_permiso(conn):
    admin = id_admin(conn)
    assert uno(conn, "SELECT fn_tiene_permiso(:u, 'CLI_CITAS', 'crear')", u=admin) is True  # no distingue mayúsculas
    assert uno(conn, "SELECT fn_tiene_permiso(:u, 'CLI_CITAS', 'ELIMINAR')", u=admin) is False
    assert uno(conn, "SELECT fn_tiene_permiso(:u, 'NO_EXISTE', 'LEER')", u=admin) is False


def test_usuario_inactivo_no_tiene_menu_ni_permisos(conn):
    admin = id_admin(conn)
    conn.execute(text("UPDATE usuario SET activo = false WHERE id_usuario = :u"), {"u": admin})
    assert uno(conn, "SELECT count(*) FROM fn_menu_usuario(:u)", u=admin) == 0
    assert uno(conn, "SELECT fn_tiene_permiso(:u, 'CLI_CITAS', 'LEER')", u=admin) is False


def test_desactivar_perfil_rol_o_modulo_quita_acceso(conn):
    admin = id_admin(conn)
    conn.execute(text("UPDATE modulo SET activo = false WHERE codigo = 'CLI_HISTORIAL'"))
    codigos = [r[0] for r in conn.execute(text("SELECT codigo FROM fn_menu_usuario(:u)"), {"u": admin})]
    assert "CLI_HISTORIAL" not in codigos and "CLI_CITAS" in codigos
    conn.execute(text("UPDATE rol SET activo = false WHERE nombre = 'Administrador'"))
    assert uno(conn, "SELECT count(*) FROM fn_menu_usuario(:u)", u=admin) == 0


def test_carpeta_sin_opciones_visibles_se_oculta(conn):
    admin = id_admin(conn)
    conn.execute(text("UPDATE modulo SET activo = false WHERE codigo LIKE 'SEG\\_%'"))
    codigos = [r[0] for r in conn.execute(text("SELECT codigo FROM fn_menu_usuario(:u)"), {"u": admin})]
    assert "SEGURIDAD" not in codigos and "GESTION_CLINICA" in codigos


# ---------- reglas del menú (triggers) ----------

def test_menu_de_dos_niveles(conn):
    assert "primer nivel" in intentar(conn, "INSERT INTO modulo (id_modulo_padre, codigo, nombre, ruta) SELECT id_modulo, 'T9_X', 'x', '/t9/x' FROM modulo WHERE codigo = 'CLI_CITAS'")
    assert "ruta" in intentar(conn, "INSERT INTO modulo (id_modulo_padre, codigo, nombre) SELECT id_modulo, 'T9_Y', 'y' FROM modulo WHERE codigo = 'SEGURIDAD'")
    assert "no puede tener ruta" in intentar(conn, "UPDATE modulo SET ruta = '/x' WHERE codigo = 'SEGURIDAD'")
    assert "debe tener ruta" in intentar(conn, "UPDATE modulo SET id_modulo_padre = id_modulo WHERE codigo = 'SEGURIDAD'")  # nunca es su propio padre


def test_permisos_solo_sobre_opciones(conn):
    assert "carpetas" in intentar(
        conn,
        "INSERT INTO perfil_modulo_permiso SELECT 1, id_modulo, 1 FROM modulo WHERE codigo = 'SEGURIDAD'",
    )


# ---------- restricciones de datos ----------

def test_email_unico_sin_distinguir_mayusculas(conn):
    assert "uq_usuario_email" in intentar(
        conn,
        "INSERT INTO usuario (id_tipo_documento, documento, nombres, apellidos, email, contrasena_hash)"
        " VALUES (1, 'T9BD2', 'a', 'b', 'ADMIN@VETERINARIA.COM', 'h')",
    )


def test_valores_validos(conn):
    pid = uno(conn, "INSERT INTO propietario (id_tipo_documento, documento, nombres, apellidos) VALUES (1,'T9BD3','A','B') RETURNING id_propietario")
    assert "ck_mascota_sexo" in intentar(conn, "INSERT INTO mascota (id_propietario, nombre, especie, sexo) VALUES (:p,'x','Perro','otro')", p=pid)
    assert "uq_propietario_documento" in intentar(conn, "INSERT INTO propietario (id_tipo_documento, documento, nombres, apellidos) VALUES (1,'T9BD3','A','B')")
    assert "motivo_consulta" in intentar(
        conn,
        "INSERT INTO cita (id_mascota, id_veterinario, id_estado_cita, fecha_hora) VALUES (1, 1, 1, now())",
    )


# ---------- citas e historial ----------

def test_fn_completar_cita_es_atomica(conn):
    cita = nueva_cita(conn)
    historial = uno(conn, "SELECT fn_completar_cita(:c, 'Sano', NULL, 'Ok')", c=cita)
    assert uno(conn, "SELECT e.nombre FROM cita c JOIN estado_cita e USING (id_estado_cita) WHERE c.id_cita = :c", c=cita) == "completada"
    assert uno(conn, "SELECT diagnostico FROM historial_clinico WHERE id_historial_clinico = :h", h=historial) == "Sano"
    assert "pendientes" in intentar(conn, "SELECT fn_completar_cita(:c, 'otra vez', NULL, NULL)", c=cita)
    assert "no existe" in intentar(conn, "SELECT fn_completar_cita(99999999, 'x', NULL, NULL)")


def test_historial_inmutable_y_solo_para_citas_completadas(conn):
    pendiente = nueva_cita(conn)
    assert "completadas" in intentar(conn, "INSERT INTO historial_clinico (id_cita, diagnostico) VALUES (:c, 'x')", c=pendiente)
    completada = nueva_cita(conn, "completada")
    conn.execute(text("INSERT INTO historial_clinico (id_cita, diagnostico) VALUES (:c, 'x')"), {"c": completada})
    assert "solo consulta" in intentar(conn, "UPDATE historial_clinico SET diagnostico = 'y' WHERE id_cita = :c", c=completada)
    assert "solo consulta" in intentar(conn, "DELETE FROM historial_clinico WHERE id_cita = :c", c=completada)
    assert "uq_historial_cita" in intentar(conn, "INSERT INTO historial_clinico (id_cita, diagnostico) VALUES (:c, 'duplicado')", c=completada)


def test_estados_finales_de_la_cita(conn):
    cancelada = nueva_cita(conn, "cancelada")
    assert "cancelada no se puede modificar" in intentar(
        conn, "UPDATE cita SET id_estado_cita = :e WHERE id_cita = :c", e=estado(conn, "pendiente"), c=cancelada
    )
    pendiente = nueva_cita(conn)
    conn.execute(text("UPDATE cita SET id_estado_cita = :e WHERE id_cita = :c"), {"e": estado(conn, "cancelada"), "c": pendiente})


def test_cita_solo_a_veterinario_activo(conn):
    vet = veterinario_activo(conn)
    conn.execute(text("UPDATE usuario SET activo = false WHERE id_usuario = (SELECT id_usuario FROM veterinario WHERE id_veterinario = :v)"), {"v": vet})
    mascota = nuevo_propietario_y_mascota(conn)
    assert "inactivo" in intentar(
        conn,
        "INSERT INTO cita (id_mascota, id_veterinario, id_estado_cita, fecha_hora, motivo_consulta) VALUES (:m, :v, 1, now(), 'x')",
        m=mascota, v=vet,
    )


def test_fn_crear_veterinario_valida_el_perfil(conn):
    msg = intentar(
        conn,
        "SELECT fn_crear_veterinario(1,'T9BD9','a','b','t9bd9@dogato-prueba.com',NULL,NULL,'h',NULL,NULL,"
        "(SELECT id_perfil FROM perfil WHERE nombre = 'Administrador del sistema'))",
    )
    assert "rol Veterinario" in msg
