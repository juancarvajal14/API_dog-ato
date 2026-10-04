# DOG-ATO — Contexto del proyecto (leer primero)

> Documento pensado para que cualquier persona o modelo de IA entienda el proyecto sin más contexto.
> Para instalar el proyecto en otro PC: `INSTALACION_COMPANEROS.md` (paso a paso, apto para que lo ejecute una IA).
> Última actualización: 2026-10-02. Historial de cambios del modelo de datos: `docs/CAMBIOS_BD.md`. Plan de trabajo: `docs/PLAN_FASES.md`.

## 1. Qué es
Plataforma web de gestión para una clínica veterinaria (proyecto académico, materia Bases de Datos 2, Colombia; equipo de 3 integrantes). Registra propietarios, mascotas, veterinarios, citas e historial clínico.
**Los únicos usuarios del sistema son administradores y veterinarios.** Los propietarios NO tienen cuenta; los registra el personal.
Es un MVP: lo necesario y funcionando, sin sobre-ingeniería.

## 2. Corrección del profesor (el cambio de fondo)
La gestión de **módulos (menú de navegación), roles y permisos debe vivir en la base de datos**, no en el backend ni en el frontend. Los permisos se manejan por acción CRUD separada (CREAR, LEER, ACTUALIZAR, ELIMINAR).
Además, la rúbrica del primer parcial (sección *Fortalecimiento Bases de Datos Relacionales*, 5.0) exige: MR en 3FN (0.5), scripts (0.5), **autenticación funcional que despliega el menú de navegación** (1.0), **Redis instalado en la máquina de cada integrante** (1.0), cada integrante **accede a Redis y ejecuta ≥ 3 instrucciones** (1.0) y **autenticación de usuario/contraseña en Redis desde la interfaz** (1.0).

## 3. Stack
| Capa | Tecnología | Ubicación |
|---|---|---|
| BD | PostgreSQL 18 (local, probado en 17 y 18; mínimo 13) | `db/DDL.sql` |
| Caché de login | Redis nativo en WSL2 (Ubuntu), sin Docker (guía: `docs/REDIS_WSL.md`) | solo para login |
| Backend | Python + FastAPI + SQLAlchemy 2 + psycopg 3 | `C:\Users\gh0st\Desktop\API_dog-ato` (este repo) |
| Frontend | React 19 + Vite + Tailwind 4 + framer-motion + lucide-react | `C:\Users\gh0st\Desktop\APP_dog-ato` |
| Despliegue | Vercel (propuesta); front en https://appdog-ato.vercel.app (versión mockup) | — |

## 4. Base de datos (fuente de verdad: `db/DDL.sql`, único .sql del repo; modelo ER en `docs/modelo_er.md`)
Script único: borra y recrea la BD `dogato` (¡solo desarrollo!), crea estructura, funciones, triggers, seguridad y datos demo. Ejecutar:
`psql -U postgres -f db/DDL.sql` (Windows: `& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -f ...`). Requiere psql (usa `\connect`); no sirve la Query Tool de pgAdmin.

### Tablas (PK `id_<tabla>` GENERATED ALWAYS AS IDENTITY, INTEGER)
- **Seguridad:** `rol` → `perfil` (id_rol); `modulo` (menú: `codigo` único, `ruta`, `icono`, `orden`, `id_modulo_padre`; sin ruta = carpeta, con ruta = pantalla; solo 2 niveles); `permiso` (CREAR, LEER, ACTUALIZAR, ELIMINAR); `perfil_modulo_permiso` (perfil, módulo, permiso). `usuario_perfil` une usuario ↔ perfil (N:M).
- **Personas:** `usuario` (id_tipo_documento, documento, nombres, apellidos, email, telefono, direccion, `contrasena_hash` bcrypt, activo); `veterinario` (id_usuario 1:1, especialidad, registro_profesional); `propietario` (sin cuenta).
- **Negocio:** `mascota` (sexo `macho|hembra`); `cita` (id_mascota, id_veterinario, id_estado_cita, fecha_hora, motivo_consulta NOT NULL); `historial_clinico` (id_cita UNIQUE, diagnostico, tratamiento, observaciones).
- **Catálogos:** `tipo_documento` (CC, TI, CE, PA), `estado_cita` (`pendiente`, `completada`, `cancelada`).
- Todos los "estado" son `activo BOOLEAN`.

### Lógica en la BD (el backend debe usarla, no duplicarla)
| Objeto | Para qué |
|---|---|
| `fn_menu_usuario(id_usuario)` | Menú del usuario: opciones con LEER + carpetas que las contienen; devuelve `permisos[]` por opción. El backend arma el árbol con `id_modulo_padre` y `orden`. |
| `fn_permisos_usuario(id_usuario)` | Pares (módulo, permiso) vigentes: usuario, perfil, rol y módulo activos. |
| `fn_tiene_permiso(id_usuario, 'CLI_CITAS', 'CREAR')` | Autorización puntual. |
| `v_matriz_permisos` | Matriz perfil × módulo × permiso (pantalla "Módulos y permisos"). |
| `fn_crear_veterinario(...)` | Alta atómica usuario + perfil + datos profesionales (recibe la contraseña ya hasheada). |
| `fn_completar_cita(id_cita, diag, trat, obs)` | Cambia la cita a `completada` y crea el historial en una transacción. |
| Triggers | Menú de 2 niveles; permisos solo sobre opciones con ruta; cita nueva solo a veterinario activo; `completada`/`cancelada` son estados finales; historial solo para citas completadas y de solo lectura. |

### Códigos de módulo (clave estable para backend/frontend)
`SEGURIDAD` (carpeta) → `SEG_VETERINARIOS`, `SEG_ROLES`, `SEG_PERFILES`, `SEG_MODULOS`.
`GESTION_CLINICA` (carpeta) → `CLI_PROPIETARIOS`, `CLI_MASCOTAS`, `CLI_CITAS`, `CLI_HISTORIAL`.

### Permisos sembrados
- Perfil **Administrador del sistema** (rol Administrador): CREAR/LEER/ACTUALIZAR en las 4 opciones de Seguridad y en Propietarios, Mascotas, Citas; solo LEER en Historial.
- Perfil **Médico veterinario** (rol Veterinario): CREAR/LEER/ACTUALIZAR en Propietarios, Mascotas, Citas; solo LEER en Historial. Sin Seguridad.
- ELIMINAR no está asignado a nadie (se activa/desactiva en lugar de borrar). Completar/cancelar cita = ACTUALIZAR sobre `CLI_CITAS`. El historial se escribe al completar la cita.

### Cuentas de desarrollo
`admin@veterinaria.com / Admin12345*` (administrador). `andres.gomez@dogato.com`, `laura.martinez@dogato.com` / `Vet12345*` (veterinarios). `diego.salazar@dogato.com` / `Vet12345*` (veterinario **inactivo**). Datos demo: 6 propietarios, 10 mascotas, 10 citas, 4 historiales.

## 5. Redis (solo login)
- **Redis nativo dentro de WSL2 (Ubuntu), NO en Docker** (decisión del equipo: así lo enseñó el profesor y todos los integrantes deben poder reproducirlo). Instalación y operación: `docs/REDIS_WSL.md`. Se enciende con `sudo service redis-server start` (dentro de Ubuntu) y escucha en 127.0.0.1:6379; el API en Windows lo alcanza en `localhost` por el reenvío de puertos de WSL2.
- Seguridad: usuario anónimo `default` deshabilitado y usuario ACL `dogato_api` con la contraseña definida en `/etc/redis/redis.conf`; el API usa las mismas credenciales desde `.env` (`REDIS_USER`, `REDIS_PASSWORD`, `REDIS_HOST`, `REDIS_PORT`).
- Acceso por consola (en Ubuntu): `redis-cli --user dogato_api --pass <clave> --no-auth-warning`.
- Se probó una versión con Docker y se descartó; no debe haber `docker-compose.yml` para Redis.
- Diseño (prefijo `dogato:`): `cred:{email}` caché de credenciales (TTL 10 min); `sesion:{token}` sesión con usuario, menú y permisos (TTL 8 h renovable); `intentos:{email}` intentos fallidos (bloqueo tras 5, TTL 15 min). Token opaco (`secrets.token_urlsafe`) en `Authorization: Bearer`, no JWT. Logout borra la sesión. Si cambian permisos o estado de un usuario, se borran sus sesiones. Si Redis cae, el login funciona contra Postgres.
- Postgres sigue siendo la fuente de verdad; Redis nunca guarda datos de negocio.

## 6. Estado actual del código (2026-10-02)
- **BD:** hecha y probada (Postgres 17 y 18, ejecutable repetidas veces).
- **Redis:** pendiente de instalar en WSL en cada máquina (Fase 1; se retiró la prueba en Docker).
- **API (este repo):** Fase 2 implementada. Código vigente: `core/` (config, database, redis_client, security, deps, errors), `repositories/auth_repository.py`, `services/auth_service.py`, `schemas/auth.py`, `routers/auth.py`, `main.py`, pruebas en `tests/test_auth.py`. Endpoints: `POST /auth/login`, `GET /auth/me`, `POST /auth/logout`, `GET /health`. El menú, los permisos y los roles salen de las funciones de la BD; la sesión (token opaco), la caché de credenciales y los intentos fallidos viven en Redis. `require_permiso("CLI_CITAS","CREAR")` protege endpoints. `auth_service.invalidar_usuario(id, email)` cierra sus sesiones (usar al cambiar permisos/perfil/estado/contraseña).
  **Fase 5 implementada:** `routers/` + `services/` + `models/` + `schemas/` para `propietarios`, `mascotas`, `citas` (incluye `/cancelar` y `/completar`), `historial` (solo lectura), `veterinarios` (crear, listar, `PATCH /{id}/estado`) y `catalogos/*` (tipos de documento, propietarios con sus mascotas, veterinarios activos, perfiles de veterinario). Contrato de la API en el vocabulario del frontend: `id`, `nombre`/`apellido` (la BD guarda `nombres`/`apellidos`), `fecha` (BD `fecha_hora`), `estado` como texto, y objetos anidados (`mascota`, `propietario`, `veterinario`) para que cada pantalla dependa solo de su endpoint. Los errores de restricciones y triggers de la BD se traducen en `core/db_errors.py`. Sin endpoints DELETE.
  **Fase 6 implementada:** `routers/{roles,perfiles,modulos}.py` + `services/seguridad_service.py` + `models/seguridad.py`. Roles/perfiles/módulos: listar, crear, editar y `PATCH /{id}/estado` (sin DELETE); matriz `GET|PUT /perfiles/{id}/permisos` (mapa `{CODIGO_MODULO: [PERMISOS]}`, reemplazo completo, exige LEER para cualquier otro permiso y solo sobre opciones con ruta); `GET /modulos/permisos`. Protecciones anti-bloqueo y de elementos del sistema documentadas en `docs/PLAN_FASES.md`. Tras cada cambio se sincroniza Redis (`auth_service.invalidar_usuarios` / `invalidar_todas` / `refrescar_sesion`).
  Frontend: `src/features/seguridad/` (RolesTab, PerfilesTab, ModulosTab → MatrizPermisos + CatalogoModulos, formularios) y `src/config/iconos.js`; `AuthContext.actualizarSesion()` recarga menú/permisos tras guardar.
  Si Redis cae: se omiten caché y bloqueo, pero el login responde 503 porque las sesiones solo existen en Redis.
  Pruebas: `venv\Scripts\python -m pytest tests -q` (requieren Postgres con la BD demo completa y Redis encendido). Ejecutar API: `venv\Scripts\python -m uvicorn main:app --reload` → Swagger en http://localhost:8000/docs.
- **Frontend (Fase 3 hecha):** el login y el menú ya son reales. `src/api/` (cliente HTTP con token Bearer), `AuthContext` (login/logout/`/auth/me`, `puede(modulo, permiso)`; en `localStorage` solo token + origen), `Sidebar` y `DashboardPage` dibujan el menú que llega de la BD, `src/config/modulos.jsx` asocia `codigo` de módulo → pantalla e icono (módulos sin pantalla muestran "en construcción"). La sidebar muestra "Credenciales validadas desde Redis/PostgreSQL" (campo `origen_credenciales` del login) para la demo. `VITE_API_URL` en `.env.local` (ejemplo en `.env.example`; configurarlo también en Vercel).
  **Fase 5 hecha:** `DataContext` y `mockData` ya no existen; cada pestaña usa `useRecurso(<funcion de src/api/recursos.js>)` con estados de carga/error (`components/ui/Estados.jsx`); los formularios (propietario con tipo de documento, mascota, cita, completar cita, veterinario) envían al API y muestran sus errores; botones según permisos. Pendiente opcional: editar registros desde la interfaz (el API ya tiene PUT), paginación.

## 7. Convenciones para el API nuevo
- Capas: `routers/` (HTTP, solo validación de permisos y delegación) → `services/` (reglas de negocio y acceso a datos con los modelos de `models/`; `repositories/` solo se usa para el SQL de autenticación) ; `schemas/` Pydantic; `core/` (config, database, redis, security, deps, errors, db_errors).
- Las reglas de integridad ya viven en la BD (triggers/funciones): el servicio las usa (`fn_completar_cita`, `fn_crear_veterinario`) y traduce sus errores; no se duplican en Python.
- **Windows y tildes:** el script SQL debe fijar `\encoding UTF8` DESPUÉS de `\connect` (ya está); si no, los textos con tilde se guardan dañados ("MÃ©dico").
- Cada endpoint protegido usa `require_permiso("<CODIGO_MODULO>", "<PERMISO>")` basado en los permisos de la sesión en Redis.
- La verificación bcrypt se hace en Python (el seed usa pgcrypto `$2a$`, compatible).
- Mapear nombres de la BD al contrato de la API de forma explícita y documentarlo en Swagger.
- Variables en `.env` (no se versiona; ejemplo en `.env.example`).

## 7b. ⏸️ Propuesta EN STAND BY: usuarios que no son veterinarios (sin cambiar la BD)
Estado: **propuesta, NO implementada; pendiente de revisión del equipo. Recordarla al terminar la Fase 5 y al iniciar la Fase 6.**
- El esquema ya lo permite: `usuario` + `usuario_perfil` sirven para cualquier perfil; solo los veterinarios necesitan fila en `veterinario`.
- API: módulo `usuarios` — `POST /usuarios` (crea usuario + asigna el perfil elegido en una transacción; si el rol del perfil es Veterinario crea también la fila `veterinario` con `fn_crear_veterinario`), `GET /usuarios`, activar/desactivar (invalidando sesiones con `auth_service.invalidar_usuario`). Permiso: reutilizar `SEG_VETERINARIOS`, renombrando su etiqueta a "Usuarios" con un `UPDATE` de datos en el seed (no cambia la estructura).
- Frontend: la pantalla "Veterinarios" pasa a "Usuarios", con selector de perfil.
- Alternativa: asignar perfiles a usuarios existentes desde la pantalla Perfiles.
- Consecuencia: el personal sin fila `veterinario` no puede recibir citas (correcto).

## 8. Decisiones abiertas
1. Rol vs. perfil se solapan (rol 1:N perfil; permisos cuelgan del perfil). Se dejó como lo diseñó el equipo.
2. Falta definir quién crea usuarios administradores (hoy "Veterinarios" solo crea el rol Veterinario).
3. ~~Un veterinario necesita ver la lista de veterinarios para elegir en Citas~~ — RESUELTO con `GET /catalogos/veterinarios` (exige CREAR en Citas).
4. No hay regla de citas solapadas por veterinario (opcional).
5. El documento `Evaluacion_BD2` (secciones 7, 8, 9, stack, objetivo) debe actualizarse; su objetivo menciona "enfermedades", que no existe como tabla.

## 8b. Estado de verificación (2026-10-04)
48 pruebas automáticas del API verdes (BD, login, negocio, seguridad) + recorrido end to end de 26 pasos en Chrome (login, los 8 módulos, crear propietario/mascota/cita, completar → historial, cancelar, crear veterinario, perfiles, matriz de permisos, módulos, veterinario con menú reducido, Redis en el 2.º login). Detalle y pendientes: `docs/ANALISIS_FINAL.md`.

## 9. Cómo levantar todo (desarrollo)
1. `psql -U postgres -f db/DDL.sql`
2. Copiar `.env.example` → `.env` y completar `DATABASE_URL` y contraseñas de Redis.
3. Redis: abrir Ubuntu (WSL) y `sudo service redis-server start` (primera vez: seguir `docs/REDIS_WSL.md`)
4. API: `python -m venv venv`, activar, `pip install -r requirements.txt`, `uvicorn main:app --reload`.
5. Frontend: `npm install`, copiar `.env.example` → `.env.local`, `npm run dev` (http://localhost:5173). Cuentas de login en la sección 4.
