"""Pruebas de integración del login: requieren Postgres (BD dogato con datos demo) y Redis encendidos."""
import pytest
from fastapi import Depends
from fastapi.testclient import TestClient

from core import redis_client as rc
from core.deps import require_permiso
from main import app
from services import auth_service

ADMIN = ("admin@veterinaria.com", "Admin12345*")
VET = ("andres.gomez@dogato.com", "Vet12345*")
VET_INACTIVO = ("diego.salazar@dogato.com", "Vet12345*")


@app.get("/_test/seg-veterinarios", include_in_schema=False)
def _ruta_solo_admin(_=Depends(require_permiso("SEG_VETERINARIOS", "LEER"))):
    return {"ok": True}


@app.get("/_test/citas-eliminar", include_in_schema=False)
def _ruta_sin_permiso(_=Depends(require_permiso("CLI_CITAS", "ELIMINAR"))):
    return {"ok": True}


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def limpiar_redis():
    def limpiar():
        for patron in ("dogato:intentos:*", "dogato:cred:*"):
            for k in rc.cliente.scan_iter(patron):
                rc.cliente.delete(k)

    limpiar()
    yield
    limpiar()


def login(client, cuenta):
    return client.post("/auth/login", json={"email": cuenta[0], "password": cuenta[1]})


def cabecera(token):
    return {"Authorization": f"Bearer {token}"}


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "postgres": "ok", "redis": "ok"}


def test_login_admin_devuelve_menu_completo_y_guarda_sesion_en_redis(client):
    r = login(client, ADMIN)
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["usuario"]["roles"] == ["Administrador"]
    carpetas = {c["codigo"]: [h["codigo"] for h in c["hijos"]] for c in cuerpo["menu"]}
    assert carpetas == {
        "SEGURIDAD": ["SEG_VETERINARIOS", "SEG_ROLES", "SEG_PERFILES", "SEG_MODULOS"],
        "GESTION_CLINICA": ["CLI_PROPIETARIOS", "CLI_MASCOTAS", "CLI_CITAS", "CLI_HISTORIAL"],
    }
    assert cuerpo["permisos"]["CLI_HISTORIAL"] == ["LEER"]
    assert rc.cliente.exists(rc.clave_sesion(cuerpo["access_token"])) == 1
    assert rc.cliente.ttl(rc.clave_sesion(cuerpo["access_token"])) > 0


def test_login_veterinario_no_ve_seguridad(client):
    cuerpo = login(client, VET).json()
    assert [c["codigo"] for c in cuerpo["menu"]] == ["GESTION_CLINICA"]
    assert "SEG_VETERINARIOS" not in cuerpo["permisos"]


def test_login_cachea_credenciales_en_redis(client):
    login(client, VET)
    cache = rc.cliente.hgetall(rc.clave_credenciales(VET[0]))
    assert cache["email"] == VET[0]
    assert cache["hash"].startswith("$2")
    # segundo login atendido desde la caché
    assert login(client, VET).status_code == 200


def test_origen_credenciales_primer_login_postgres_y_luego_redis(client):
    assert login(client, VET).json()["origen_credenciales"] == "postgres"
    assert login(client, VET).json()["origen_credenciales"] == "redis"
    # si la caché vence o se invalida, vuelve a Postgres
    rc.cliente.delete(rc.clave_credenciales(VET[0]))
    assert login(client, VET).json()["origen_credenciales"] == "postgres"


def test_email_no_distingue_mayusculas(client):
    r = client.post("/auth/login", json={"email": "ADMIN@Veterinaria.com", "password": ADMIN[1]})
    assert r.status_code == 200


def test_contrasena_incorrecta(client):
    r = login(client, (ADMIN[0], "mala"))
    assert r.status_code == 401
    assert r.json()["detail"] == "Correo o contraseña incorrectos"


def test_correo_inexistente_responde_igual(client):
    r = login(client, ("nadie@nada.com", "x"))
    assert r.status_code == 401
    assert r.json()["detail"] == "Correo o contraseña incorrectos"


def test_usuario_inactivo(client):
    assert login(client, VET_INACTIVO).status_code == 403


def test_bloqueo_tras_cinco_intentos(client):
    for _ in range(5):
        assert login(client, (VET[0], "mala")).status_code == 401
    r = login(client, VET)  # aun con la clave correcta
    assert r.status_code == 429
    assert "Retry-After" in r.headers


def test_login_correcto_reinicia_intentos(client):
    for _ in range(3):
        login(client, (VET[0], "mala"))
    assert login(client, VET).status_code == 200
    assert rc.cliente.exists(rc.clave_intentos(VET[0])) == 0


def test_me_y_logout_eliminan_la_sesion(client):
    token = login(client, ADMIN).json()["access_token"]
    assert client.get("/auth/me", headers=cabecera(token)).json()["usuario"]["email"] == ADMIN[0]
    assert client.post("/auth/logout", headers=cabecera(token)).status_code == 204
    assert rc.cliente.exists(rc.clave_sesion(token)) == 0
    assert client.get("/auth/me", headers=cabecera(token)).status_code == 401


def test_sin_token_o_token_falso(client):
    assert client.get("/auth/me").status_code == 401
    assert client.get("/auth/me", headers=cabecera("inventado")).status_code == 401


def test_require_permiso(client):
    admin = login(client, ADMIN).json()["access_token"]
    vet = login(client, VET).json()["access_token"]
    assert client.get("/_test/seg-veterinarios", headers=cabecera(admin)).status_code == 200
    assert client.get("/_test/seg-veterinarios", headers=cabecera(vet)).status_code == 403
    # ELIMINAR no está asignado a ningún perfil
    assert client.get("/_test/citas-eliminar", headers=cabecera(admin)).status_code == 403


def test_invalidar_usuario_cierra_todas_sus_sesiones(client):
    t1 = login(client, VET).json()["access_token"]
    t2 = login(client, VET).json()["access_token"]
    id_usuario = client.get("/auth/me", headers=cabecera(t1)).json()["usuario"]["id_usuario"]
    auth_service.invalidar_usuario(id_usuario, VET[0])
    assert client.get("/auth/me", headers=cabecera(t1)).status_code == 401
    assert client.get("/auth/me", headers=cabecera(t2)).status_code == 401
    assert rc.cliente.exists(rc.clave_credenciales(VET[0])) == 0
