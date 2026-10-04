# DOG-ATO · Plan de ejecución por fases

Prioridad = rúbrica del primer parcial, sección **Fortalecimiento Bases de Datos Relacionales** (nota sobre 5.0).

| Criterio de la rúbrica | Peso | Estado | Fase |
|---|---|---|---|
| MR – 3FN | 0.5 | Modelo listo (`db/DDL.sql`) y diagrama ER generado (`docs/modelo_er.png`); falta pegarlo en el documento | 6 |
| Scripts | 0.5 | Listo (script único y probado); falta actualizar sección 8 del documento | 6 |
| Autenticación funcional para desplegar el menú de navegación | 1.0 | Pendiente | 2, 3, 4 |
| Instalación y configuración de Redis en la máquina de cada integrante | 1.0 | Pendiente: Redis **nativo en WSL (Ubuntu)** en cada máquina | 1 |
| Cada integrante accede a Redis y ejecuta ≥ 3 instrucciones | 1.0 | Guion listo (ver Fase 1) | 1 |
| Autenticación de usuario y contraseña en Redis desde la interfaz | 1.0 | Pendiente | 3, 4 |

## Decisiones de arquitectura
- **PostgreSQL = fuente de verdad** (usuarios, perfiles, módulos, permisos). Redis solo para login.
- **Redis en login** (todo con prefijo `dogato:`):
  - `dogato:cred:{email}` → caché de credenciales (id_usuario, hash bcrypt, activo). TTL 10 min.
  - `dogato:sesion:{token}` → sesión: usuario, menú y permisos (de `fn_menu_usuario`). TTL 8 h, se renueva con uso.
  - `dogato:intentos:{email}` → intentos fallidos (bloqueo temporal tras 5). TTL 15 min.
  - `logout` borra la sesión. Si cambian permisos/estado de un usuario, la API borra sus sesiones y su caché.
  - Si Redis cae: la caché de credenciales y el bloqueo por intentos se omiten (se consulta Postgres), pero **las sesiones viven solo en Redis**, así que el login responde 503 "servicio de sesiones no disponible".
- **Token opaco** (`secrets.token_urlsafe`) enviado como `Authorization: Bearer`, en vez de JWT: así la sesión vive de verdad en Redis y se puede ver con `redis-cli`.
- **Autorización**: cada endpoint exige `require_permiso("CLI_CITAS", "CREAR")`, validado con los permisos de la sesión (que salen de la BD).
- Redis **nativo en WSL2 (Ubuntu)**, sin Docker, tal como lo enseñó el profesor. Protegido con **usuario y contraseña (ACL)**; el usuario anónimo `default` queda deshabilitado. El API (en Windows) lo alcanza en `localhost:6379` porque WSL2 reenvía el puerto.

## Fase 0 · Base de datos ✅
Script único `DDL.sql` (Postgres ≥ 13), con datos demo. Todos los compañeros lo ejecutan.

## Fase 1 · Instalación de Redis nativo en WSL (prioridad 1) 🟡
Cada integrante, en su máquina (guía completa con comandos en `REDIS_WSL.md`):
1. Instalar Ubuntu en WSL: `wsl --install -d Ubuntu` (reiniciar si lo pide, crear usuario y contraseña de Linux).
2. Dentro de Ubuntu: `sudo apt update && sudo apt install -y redis-server`.
3. Configurar usuario/contraseña (ACL) en `/etc/redis/redis.conf` y arrancar con `sudo service redis-server start`.
4. En el `.env` del API poner los mismos `REDIS_USER` / `REDIS_PASSWORD`.
5. Evidencia (capturas): `redis-server --version`, `sudo service redis-server status` y la conexión autenticada:
   ```
   redis-cli --user dogato_api --pass <su_clave> --no-auth-warning
   PING                                  → PONG
   SET dogato:prueba "hola" EX 60        → OK
   GET dogato:prueba                     → "hola"
   TTL dogato:prueba                     → ~59
   HSET dogato:sesion:demo email a@b.com
   HGETALL dogato:sesion:demo
   ACL WHOAMI                            → "dogato_api"
   ```
   También mostrar que sin credenciales falla: `redis-cli ping` → `NOAUTH Authentication required`.

## Fase 2 · Núcleo del API y login con Redis (prioridad 1) 🟡 (código listo, falta correr pruebas con la BD completa)
- ✅ API viejo eliminado (ya no existe `legacy_v1/`). Estructura `core/ repositories/ services/ routers/ schemas/ tests/`.
- ✅ `requirements.txt` con `redis` y `bcrypt`; `requirements-dev.txt` con `pytest`/`httpx`; entorno `venv/`.
- ✅ `core/redis_client.py`, `core/security.py` (bcrypt), `core/config.py`, `core/errors.py`, `core/deps.py`.
- ✅ `POST /auth/login`, `POST /auth/logout`, `GET /auth/me` (usuario + menú en árbol + permisos), `GET /health` (Postgres y Redis), CORS.
- ✅ `get_sesion` y `require_permiso(modulo, permiso)`; `invalidar_usuario()` para Fase 5/6.
- ✅ Pruebas de integración `tests/test_auth.py` (14 casos: menú admin/veterinario, caché en Redis, mayúsculas, clave mala, correo inexistente, inactivo, bloqueo a 5 intentos, logout, token falso, permisos, invalidación).
- ⏳ Los modelos SQLAlchemy de negocio se crean en la Fase 5 junto a cada CRUD (el login usa las funciones de la BD).

## Fase 3 · Frontend: login y menú dinámico (prioridad 1) ✅ (falta la prueba visual en el navegador)
- ✅ `src/api/cliente.js` y `src/api/auth.js` (fetch con token Bearer, manejo de 401/red caída), `VITE_API_URL` en `.env.local` / `.env.example`.
- ✅ `AuthContext` real: login contra `/auth/login`; en `localStorage` solo se guarda el token (+ origen de credenciales); `/auth/me` al recargar; `puede(modulo, permiso)`.
- ✅ Sidebar construida desde el menú de la sesión (carpetas → opciones, iconos de la BD); `navegacion.js` eliminado; `src/config/modulos.jsx` solo asocia `codigo` → pantalla.
- ✅ Botones Nuevo/Completar/Cancelar/Activar visibles según permisos; botón de eliminar veterinario retirado.
- ✅ Indicador "Credenciales validadas desde Redis / PostgreSQL" (campo `origen_credenciales` del login) para la demostración.
- ✅ CORS en el API (http://localhost:5173).
- Las pantallas de negocio siguen con datos en memoria hasta la Fase 5; Roles, Perfiles y Módulos muestran "Módulo en construcción" (Fase 6).

## Fase 4 · Evidencia de la rúbrica ✅ (guion listo en `DEMO_RUBRICA.md`; el ensayo end to end se hace al terminar las fases)
- Guion paso a paso por criterio de la rúbrica (partes A–F), comandos y resultados esperados, preguntas probables del profesor, lista de capturas por integrante y tabla de problemas.
- Flujo clave: login → `KEYS dogato:*` / `HGETALL dogato:cred:<correo>` / `GET dogato:sesion:<token>` → indicador PostgreSQL → Redis → bloqueo por intentos → logout (la sesión desaparece) → Redis apagado (503).
- Pendiente del equipo: diagrama ERD en el documento (sección 7) y capturas de cada integrante.

## Fase 5 · CRUD de negocio ✅ (falta la prueba visual en el navegador)
- ✅ API: `propietarios` (GET/POST/PUT), `mascotas` (GET/POST/PUT), `citas` (GET/POST, `/cancelar`, `/completar` → `fn_completar_cita`), `historial` (solo GET), `veterinarios` (GET/POST → `fn_crear_veterinario`, `PATCH /estado` que invalida sesiones en Redis), `catalogos/*` (listas de apoyo para formularios con permisos mínimos). No hay DELETE en ningún módulo (ELIMINAR no está asignado).
- ✅ Errores de la BD (duplicados, FK, triggers) se traducen a mensajes en español (409/400/422) con `core/db_errors.py`.
- ✅ Modelos SQLAlchemy de negocio en `models/`; reglas en `services/`; permisos con `require_permiso` en cada endpoint.
- ✅ Frontend: `DataContext` y `mockData` eliminados; cada pestaña carga su lista del API (`src/api/recursos.js`, `useRecurso`), con estados de carga/error y avisos de fallo; formularios con tipo de documento y manejo de errores.
- ✅ Pruebas: `tests/test_negocio.py` (propietarios, mascotas, veterinarios, citas, historial, catálogos, permisos) — 24 pruebas en total, todas verdes sobre una BD recién creada.
- Pendiente de Fase 5 (opcional): editar propietarios/mascotas desde la interfaz (el API ya tiene PUT), paginación.
- ⏸️ **Recordatorio:** la propuesta de "usuarios que no son veterinarios" sigue EN STAND BY (ver `CONTEXT.md` sección 7b). Revisarla con el equipo antes de la Fase 6.

## Fase 6 · Seguridad y documentación 🟡 (pantallas listas; documento pendiente)
- ✅ API de seguridad: `roles`, `perfiles`, `modulos` (GET/POST/PUT y `PATCH /estado`), `modulos/permisos` y la matriz `GET|PUT /perfiles/{id}/permisos` (reemplazo completo en una transacción; los triggers de la BD validan el árbol del menú). Sin DELETE: se activa/desactiva.
- ✅ Protecciones: no se renombran ni desactivan los roles del sistema (Administrador, Veterinario) ni los módulos `SEGURIDAD`/`SEG_*`; el administrador no puede desactivar su propio rol o perfil, cambiarle el rol, ni quitarle a su perfil LEER/ACTUALIZAR de «Módulos y permisos»; no se asignan permisos sin LEER ni sobre carpetas.
- ✅ Sincronización con Redis: al cambiar un perfil/rol se cierran las sesiones de sus usuarios; al cambiar un módulo, las de todos; la sesión de quien hizo el cambio se recalcula en el momento (`refrescar_sesion`).
- ✅ Frontend: pantallas Roles, Perfiles y «Módulos y permisos» (matriz de casillas por perfil + catálogo del menú con alta/edición/estado). Una opción nueva del menú se ve en la barra pero muestra «Módulo en construcción» hasta que el equipo programe su pantalla (se asocia en `src/config/modulos.jsx`).
- ✅ Pruebas: `tests/test_seguridad.py` (permisos, protecciones, árbol, matriz y sincronización de sesiones) — 32 pruebas en total, todas verdes.
- ⏳ Pendiente: actualizar `Evaluacion_BD2` (diagrama MR 3FN, sección 8 scripts, sección 9 roles/permisos, Redis en el stack, módulos y objetivos).
- ⏸️ **Sigue EN STAND BY** la propuesta de usuarios que no son veterinarios (`CONTEXT.md` sección 7b): la pantalla Perfiles ya existe, pero aún no hay forma de asignar un perfil a un usuario que no sea veterinario.

## Fase 7 · Pruebas y despliegue 🟡 (preparado; la publicación real queda a decisión del equipo)
- ✅ Pruebas: 48 en total y todas verdes sobre una BD recién creada — `test_bd.py` (funciones, triggers y restricciones; cada prueba se revierte), `test_auth.py`, `test_negocio.py`, `test_seguridad.py`. Frontend: `vite build` compila; `oxlint` sin errores.
- ✅ READMEs actualizados (API y frontend) con puesta en marcha, cuentas, pruebas y estructura.
- ✅ Script de **producción** generado desde el de desarrollo (`db/generar_produccion.py` → `db/DOG-ATO_produccion.sql`): no borra ni crea la BD, sin datos demo, y el administrador inicial se define con `-v admin_email -v admin_password`. Probado en una BD temporal (sin variables se detiene; con variables crea 1 usuario; segunda ejecución falla sin tocar nada).
- ✅ Configuración para la nube: `REDIS_SSL`, `ENTORNO=produccion` (oculta `/docs`), `CORS_ORIGINS` por variable de entorno, `?sslmode=require` documentado. Guía completa en `DESPLIEGUE.md`.
- ⏳ **Pendiente de decisión del equipo:** elegir proveedores (sugerido: Vercel + Render/Railway + Neon/Supabase + Upstash), crear las cuentas y publicar. Nada se ha publicado.
- ⏳ Pendiente (análisis final): commit en git de ambos repos, volver a ejecutar el script (tildes), actualizar `Evaluacion_BD2`, ensayo end to end con `DEMO_RUBRICA.md`.
