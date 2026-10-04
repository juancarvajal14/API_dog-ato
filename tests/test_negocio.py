"""Pruebas de integración de los módulos de negocio (Postgres con la BD demo + Redis encendidos).
Los datos que crean llevan documento 'T9...' y se borran al terminar."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from core import redis_client as rc
from core.database import engine
from main import app

ADMIN = {"email": "admin@veterinaria.com", "password": "Admin12345*"}
VET = {"email": "andres.gomez@dogato.com", "password": "Vet12345*"}
EMAIL_NUEVO_VET = "t9.vet@dogato-prueba.com"
CLAVE_NUEVO_VET = "ClaveSegura1!"


def limpiar_datos_prueba():
    with engine.begin() as c:
        # El historial es de solo lectura por trigger; se suspende únicamente para limpiar datos de prueba.
        c.execute(text("ALTER TABLE historial_clinico DISABLE TRIGGER trg_historial_valida"))
        try:
            c.execute(text("""
                DELETE FROM historial_clinico WHERE id_cita IN (
                    SELECT ci.id_cita FROM cita ci
                    JOIN mascota m ON m.id_mascota = ci.id_mascota
                    JOIN propietario p ON p.id_propietario = m.id_propietario
                    WHERE p.documento LIKE 'T9%')"""))
        finally:
            c.execute(text("ALTER TABLE historial_clinico ENABLE TRIGGER trg_historial_valida"))
        c.execute(text("""
            DELETE FROM cita WHERE id_mascota IN (
                SELECT m.id_mascota FROM mascota m JOIN propietario p ON p.id_propietario = m.id_propietario
                WHERE p.documento LIKE 'T9%')"""))
        c.execute(text("DELETE FROM mascota WHERE id_propietario IN (SELECT id_propietario FROM propietario WHERE documento LIKE 'T9%')"))
        c.execute(text("DELETE FROM propietario WHERE documento LIKE 'T9%'"))
        c.execute(text("DELETE FROM usuario_perfil WHERE id_usuario IN (SELECT id_usuario FROM usuario WHERE documento LIKE 'T9%')"))
        c.execute(text("DELETE FROM veterinario WHERE id_usuario IN (SELECT id_usuario FROM usuario WHERE documento LIKE 'T9%')"))
        c.execute(text("DELETE FROM usuario WHERE documento LIKE 'T9%'"))
    for patron in ("dogato:intentos:*", "dogato:cred:*"):
        for k in rc.cliente.scan_iter(patron):
            rc.cliente.delete(k)


@pytest.fixture(scope="module")
def client():
    limpiar_datos_prueba()
    with TestClient(app) as c:
        yield c
    limpiar_datos_prueba()


def token(client, cuenta):
    r = client.post("/auth/login", json=cuenta)
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="module")
def admin(client):
    return token(client, ADMIN)


@pytest.fixture(scope="module")
def vet(client):
    return token(client, VET)


def propietario_json(documento="T9000001", **extra):
    return {"id_tipo_documento": 1, "documento": documento, "nombre": "Prueba", "apellido": "Tester",
            "telefono": "3000000000", "email": "t9@dogato-prueba.com", "direccion": "Calle 1", **extra}


# ---------- seguridad general ----------

def test_endpoints_exigen_token(client):
    for ruta in ("/propietarios", "/mascotas", "/citas", "/historial", "/veterinarios", "/catalogos/tipos-documento"):
        assert client.get(ruta).status_code == 401, ruta


def test_veterinario_no_accede_a_seguridad(client, vet):
    assert client.get("/veterinarios", headers=vet).status_code == 403
    assert client.get("/catalogos/perfiles-veterinario", headers=vet).status_code == 403
    assert client.patch("/veterinarios/1/estado", json={"activo": False}, headers=vet).status_code == 403


def test_historial_es_solo_lectura(client, admin):
    assert client.post("/historial", json={}, headers=admin).status_code == 405
    assert client.put("/historial/1", json={}, headers=admin).status_code in (404, 405)
    assert client.delete("/historial/1", headers=admin).status_code in (404, 405)


def test_no_existen_endpoints_de_eliminar(client, admin):
    for ruta in ("/propietarios/1", "/mascotas/1", "/veterinarios/1", "/citas/1"):
        assert client.delete(ruta, headers=admin).status_code in (404, 405), ruta


# ---------- propietarios ----------

def test_propietarios_crud(client, admin, vet):
    r = client.post("/propietarios", json=propietario_json(), headers=vet)  # el veterinario puede crear
    assert r.status_code == 201, r.text
    creado = r.json()
    assert creado["tipo_documento"] == "CC" and creado["mascotas"] == []

    # documento duplicado
    r = client.post("/propietarios", json=propietario_json(), headers=admin)
    assert r.status_code == 409 and "documento" in r.json()["detail"]

    # textos vacíos se tratan como ausentes; correo inválido se rechaza
    assert client.post("/propietarios", json=propietario_json("T9000002", telefono="", direccion=""), headers=admin).status_code == 201
    assert client.post("/propietarios", json=propietario_json("T9000003", email="no-es-correo"), headers=admin).status_code == 422
    assert client.post("/propietarios", json=propietario_json("T9000004", id_tipo_documento=999), headers=admin).status_code == 400

    r = client.put(f"/propietarios/{creado['id']}", json=propietario_json(nombre="Editado"), headers=admin)
    assert r.status_code == 200 and r.json()["nombre"] == "Editado"
    assert any(p["id"] == creado["id"] for p in client.get("/propietarios", headers=vet).json())
    assert client.get("/propietarios/99999999", headers=admin).status_code == 404


# ---------- mascotas ----------

def test_mascotas(client, admin):
    pid = next(p["id"] for p in client.get("/propietarios", headers=admin).json() if p["documento"] == "T9000001")
    cuerpo = {"nombre": "Firulais", "especie": "Perro", "raza": "", "sexo": "macho",
              "fecha_nacimiento": "2022-05-01", "propietario_id": pid}
    r = client.post("/mascotas", json=cuerpo, headers=admin)
    assert r.status_code == 201, r.text
    mascota = r.json()
    assert mascota["raza"] is None and mascota["propietario"]["id"] == pid

    assert client.post("/mascotas", json={**cuerpo, "sexo": "otro"}, headers=admin).status_code == 422
    assert client.post("/mascotas", json={**cuerpo, "propietario_id": 99999999}, headers=admin).status_code == 404

    r = client.put(f"/mascotas/{mascota['id']}", json={**cuerpo, "nombre": "Rocky"}, headers=admin)
    assert r.json()["nombre"] == "Rocky"
    assert [m["id"] for m in client.get(f"/mascotas?propietario_id={pid}", headers=admin).json()] == [mascota["id"]]


# ---------- veterinarios ----------

def test_veterinarios_ciclo_completo(client, admin):
    perfiles = client.get("/catalogos/perfiles-veterinario", headers=admin).json()
    assert [p["nombre"] for p in perfiles] == ["Médico veterinario"]
    cuerpo = {"id_tipo_documento": 1, "documento": "T9100001", "nombre": "Nuevo", "apellido": "Vet",
              "telefono": "", "direccion": "Calle 2", "email": EMAIL_NUEVO_VET, "password": CLAVE_NUEVO_VET,
              "especialidad": "Cirugía", "registro_profesional": "T9-REG-1", "id_perfil": perfiles[0]["id"]}

    r = client.post("/veterinarios", json=cuerpo, headers=admin)
    assert r.status_code == 201, r.text
    nuevo = r.json()
    assert nuevo["rol"] == "veterinario" and nuevo["activo"] is True and nuevo["perfiles"] == ["Médico veterinario"]
    assert "password" not in nuevo and "contrasena_hash" not in nuevo

    # duplicados: correo y registro profesional
    r = client.post("/veterinarios", json={**cuerpo, "documento": "T9100002", "registro_profesional": "T9-REG-2"}, headers=admin)
    assert r.status_code == 409 and "correo" in r.json()["detail"]
    r = client.post("/veterinarios", json={**cuerpo, "documento": "T9100003", "email": "t9.otro@dogato-prueba.com"}, headers=admin)
    assert r.status_code == 409 and "registro" in r.json()["detail"]
    # contraseña corta y perfil que no es de veterinario
    assert client.post("/veterinarios", json={**cuerpo, "password": "corta"}, headers=admin).status_code == 422
    perfil_admin = 1  # 'Administrador del sistema'
    r = client.post("/veterinarios", json={**cuerpo, "documento": "T9100004", "email": "t9.x@dogato-prueba.com",
                                           "registro_profesional": "T9-REG-4", "id_perfil": perfil_admin}, headers=admin)
    assert r.status_code == 409 and "rol Veterinario" in r.json()["detail"]

    # el nuevo veterinario puede iniciar sesión (la contraseña quedó con hash bcrypt)
    login = client.post("/auth/login", json={"email": EMAIL_NUEVO_VET, "password": CLAVE_NUEVO_VET})
    assert login.status_code == 200
    token_nuevo = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert client.get("/auth/me", headers=token_nuevo).status_code == 200

    r = client.patch("/veterinarios/%d/estado" % nuevo["id"], json={"activo": False}, headers=admin)
    assert r.status_code == 200 and r.json()["activo"] is False

    # desactivar cierra sus sesiones y le impide volver a entrar
    assert client.get("/auth/me", headers=token_nuevo).status_code == 401
    assert client.post("/auth/login", json={"email": EMAIL_NUEVO_VET, "password": CLAVE_NUEVO_VET}).status_code == 403

    # una cita a un veterinario inactivo la rechaza la BD
    pid = next(p["id"] for p in client.get("/propietarios", headers=admin).json() if p["documento"] == "T9000001")
    mid = client.get(f"/mascotas?propietario_id={pid}", headers=admin).json()[0]["id"]
    r = client.post("/citas", json={"mascota_id": mid, "veterinario_id": nuevo["id"],
                                    "fecha": "2030-01-10T10:00", "motivo_consulta": "x"}, headers=admin)
    assert r.status_code == 409 and "inactivo" in r.json()["detail"]
    assert nuevo["id"] not in [v["id"] for v in client.get("/catalogos/veterinarios", headers=admin).json()]

    # reactivar
    assert client.patch("/veterinarios/%d/estado" % nuevo["id"], json={"activo": True}, headers=admin).json()["activo"] is True


# ---------- citas e historial ----------

def test_ciclo_de_citas_e_historial(client, admin, vet):
    pid = next(p["id"] for p in client.get("/propietarios", headers=admin).json() if p["documento"] == "T9000001")
    mid = client.get(f"/mascotas?propietario_id={pid}", headers=admin).json()[0]["id"]
    vid = client.get("/catalogos/veterinarios", headers=admin).json()[0]["id"]
    cuerpo = {"mascota_id": mid, "veterinario_id": vid, "fecha": "2030-02-01T09:30", "motivo_consulta": "Vacuna"}

    r = client.post("/citas", json=cuerpo, headers=vet)
    assert r.status_code == 201, r.text
    cita = r.json()
    assert cita["estado"] == "pendiente" and cita["mascota"]["nombre"] == "Rocky"
    assert cita["propietario"]["nombre"] == "Editado" and cita["veterinario"]["id"] == vid

    assert client.post("/citas", json={**cuerpo, "mascota_id": 99999999}, headers=admin).status_code == 404
    assert client.post("/citas", json={**cuerpo, "motivo_consulta": ""}, headers=admin).status_code == 422

    # completar genera el historial y deja la cita en estado final
    r = client.post(f"/citas/{cita['id']}/completar",
                    json={"diagnostico": "Sano", "tratamiento": "", "observaciones": "Volver en 1 año"}, headers=vet)
    assert r.status_code == 201, r.text
    h = r.json()
    assert h["cita_id"] == cita["id"] and h["tratamiento"] is None and h["mascota"]["nombre"] == "Rocky"
    assert client.post(f"/citas/{cita['id']}/completar", json={"diagnostico": "otra vez"}, headers=vet).status_code == 409
    assert client.post(f"/citas/{cita['id']}/cancelar", headers=vet).status_code == 409
    assert client.post(f"/citas/{cita['id']}/completar", json={}, headers=vet).status_code == 422
    assert client.post("/citas/99999999/completar", json={"diagnostico": "x"}, headers=vet).status_code == 404

    estado = {c["id"]: c["estado"] for c in client.get("/citas", headers=vet).json()}
    assert estado[cita["id"]] == "completada"
    assert [e["id"] for e in client.get(f"/historial?mascota_id={mid}", headers=vet).json()] == [h["id"]]

    # cancelar otra cita pendiente: no genera historial
    cita2 = client.post("/citas", json={**cuerpo, "fecha": "2030-02-02T09:30"}, headers=admin).json()
    r = client.post(f"/citas/{cita2['id']}/cancelar", headers=vet)
    assert r.status_code == 200 and r.json()["estado"] == "cancelada"
    assert client.post(f"/citas/{cita2['id']}/completar", json={"diagnostico": "x"}, headers=vet).status_code == 409
    assert len(client.get(f"/historial?mascota_id={mid}", headers=vet).json()) == 1

    # filtros
    assert all(c["estado"] == "cancelada" for c in client.get("/citas?estado=cancelada", headers=vet).json())
    assert client.get("/citas?estado=inventado", headers=vet).status_code == 422


# ---------- catálogos ----------

def test_catalogos(client, admin, vet):
    tipos = client.get("/catalogos/tipos-documento", headers=vet).json()
    assert {t["abreviacion"] for t in tipos} == {"CC", "TI", "CE", "PA"}
    props = client.get("/catalogos/propietarios", headers=vet).json()  # el veterinario crea citas/mascotas
    assert any(p["documento"] == "T9000001" and p["mascotas"] for p in props)
    assert client.get("/catalogos/veterinarios", headers=vet).status_code == 200
