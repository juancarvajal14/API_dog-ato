# DOG-ATO · API

API REST (FastAPI + SQLAlchemy) de la plataforma de gestión veterinaria DOG-ATO. PostgreSQL guarda los datos y la seguridad
(menú, roles, perfiles y permisos); Redis se usa solo para el login (sesiones, intentos fallidos y caché de credenciales).

> **¿Eres compañero y vas a instalar el proyecto? Empieza por [`INSTALACION_COMPANEROS.md`](INSTALACION_COMPANEROS.md)** (paso a paso completo, también para que lo siga una IA).
>
> Contexto completo del proyecto: [`CONTEXT.md`](CONTEXT.md) · Plan por fases: [`docs/PLAN_FASES.md`](docs/PLAN_FASES.md) ·
> Demostración de la rúbrica: [`docs/DEMO_RUBRICA.md`](docs/DEMO_RUBRICA.md) · Redis en WSL: [`docs/REDIS_WSL.md`](docs/REDIS_WSL.md) ·
> Despliegue: [`docs/DESPLIEGUE.md`](docs/DESPLIEGUE.md)

## Requisitos
PostgreSQL 13+ · Redis (nativo en WSL/Ubuntu, ver `docs/REDIS_WSL.md`) · Python 3.12+ · Node 20+ (frontend).

## Puesta en marcha (desarrollo)
1. **Base de datos** (borra y recrea `dogato` con datos demo; solo desarrollo):
   ```powershell
   & "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -f db\DDL.sql
   ```
2. **Redis** (en Ubuntu/WSL): `sudo service redis-server start`
3. **Variables:** copiar `.env.example` a `.env` y completar `DATABASE_URL` y `REDIS_PASSWORD`.
4. **API:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\python -m pip install -r requirements.txt
   .\venv\Scripts\python -m uvicorn main:app --reload
   ```
   Documentación interactiva: http://localhost:8000/docs · Estado: http://localhost:8000/health
5. **Frontend:** ver el README de `APP_dog-ato` (`npm install`, `.env.local`, `npm run dev`).

## Cuentas de desarrollo (las crea el script)
| Correo | Contraseña | Perfil |
|---|---|---|
| admin@veterinaria.com | `Admin12345*` | Administrador del sistema |
| andres.gomez@dogato.com | `Vet12345*` | Médico veterinario |
| laura.martinez@dogato.com | `Vet12345*` | Médico veterinario |
| diego.salazar@dogato.com | `Vet12345*` | Médico veterinario (inactivo) |

## Pruebas
```powershell
.\venv\Scripts\python -m pip install -r requirements-dev.txt
.\venv\Scripts\python -m pytest tests -q
```
Son pruebas de integración: necesitan Postgres con la BD demo y Redis encendidos. Los datos que crean se borran al terminar
(prefijo `T9`). Para no tocar tu BD de trabajo, créala aparte y apunta `DATABASE_URL` a ella al ejecutar `pytest`.

| Archivo | Cubre |
|---|---|
| `tests/test_bd.py` | funciones, triggers y restricciones de la BD (cada prueba se revierte) |
| `tests/test_auth.py` | login, caché y sesión en Redis, bloqueo por intentos, `require_permiso` |
| `tests/test_negocio.py` | propietarios, mascotas, veterinarios, citas, historial y catálogos |
| `tests/test_seguridad.py` | roles, perfiles, módulos, matriz de permisos y sincronización de sesiones |

## Estructura
```
core/          configuración, conexión a BD, cliente Redis, seguridad (bcrypt), dependencias de permisos, errores
models/        modelos SQLAlchemy        schemas/   contratos de entrada/salida (Pydantic)
routers/       endpoints HTTP            services/  reglas de negocio y acceso a datos
repositories/  SQL de autenticación      db/        DDL.sql (único script SQL) y generador del script de producción
tests/         pruebas                   docs/      guías, plan, modelo ER (modelo_er.md/.png)
```

## Endpoints principales
`POST /auth/login` · `GET /auth/me` · `POST /auth/logout` · `/propietarios` · `/mascotas` · `/citas` (`/cancelar`, `/completar`) ·
`/historial` (solo lectura) · `/veterinarios` · `/roles` · `/perfiles` (`/{id}/permisos`) · `/modulos` · `/catalogos/*`.
Todos (salvo el login y `/health`) exigen `Authorization: Bearer <token>` y el permiso del módulo correspondiente.
