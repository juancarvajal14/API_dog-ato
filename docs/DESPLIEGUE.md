# DOG-ATO · Guía de despliegue

> Estado: **preparado, no desplegado.** Publicar en la nube requiere cuentas y decisiones del equipo (proveedor, dominio, costos);
> nada de esto se ha publicado. Esta guía deja todo listo para hacerlo en una tarde.

## Arquitectura de producción
```
Navegador ─► Frontend estático (Vercel) ─► API FastAPI (Render / Railway / Fly) ─┬─► PostgreSQL administrado (Neon / Supabase)
                                                                                 └─► Redis administrado (Upstash)
```
Vercel solo aloja el frontend; el API necesita un servicio que ejecute Python continuamente.

> La rúbrica pide Redis **instalado en la máquina de cada integrante** (WSL). Eso es para el desarrollo y la demostración;
> en producción se usa un Redis administrado con la misma configuración (usuario + contraseña).

## 1. Base de datos
1. Crear la base `dogato` en el proveedor (no la crea el script).
2. Generar el script de producción a partir de `db/DDL.sql` (no se guarda en el repositorio): `python db/generar_produccion.py` → crea `db/DOG-ATO_produccion.sql`
3. Ejecutarlo contra la base nueva (¡define tú el correo y la contraseña del administrador!):
   ```
   psql "<cadena de conexión del proveedor>" -v admin_email='tu@correo.com' -v admin_password='<clave larga>' -f db/DOG-ATO_produccion.sql
   ```
   - No borra nada ni carga datos de demostración; si las tablas ya existen, falla sin cambiar nada.
   - Solo crea al administrador inicial. Los demás usuarios (veterinarios) se crean desde la aplicación.
   - Requiere `CREATE EXTENSION pgcrypto` (Neon y Supabase lo permiten).

## 2. Redis
Crear una base Redis (Upstash u otro) con usuario y contraseña, con TLS. Anotar host, puerto, usuario y contraseña.

## 3. API (ejemplo con Render; Railway/Fly son equivalentes)
- Servicio web desde el repositorio `API_dog-ato`, entorno Python.
- Build: `pip install -r requirements.txt`
- Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Variables de entorno:

| Variable | Valor |
|---|---|
| `DATABASE_URL` | `postgresql+psycopg://usuario:clave@host/dogato?sslmode=require` |
| `REDIS_HOST` / `REDIS_PORT` / `REDIS_USER` / `REDIS_PASSWORD` | datos del Redis administrado |
| `REDIS_SSL` | `true` |
| `ENTORNO` | `produccion` (oculta `/docs`) |
| `CORS_ORIGINS` | `["https://tu-frontend.vercel.app"]` (lista JSON con el dominio real del frontend) |

- Verificar: `https://<tu-api>/health` → `{"status":"ok","postgres":"ok","redis":"ok"}`.

## 4. Frontend (Vercel)
- Importar el repositorio `APP_dog-ato` (Vite se detecta solo: build `npm run build`, salida `dist`).
- Variable de entorno: `VITE_API_URL=https://<tu-api>` (sin barra final). Hay que **redeplegar** si se cambia.

## 5. Lista de verificación antes de publicar
- [ ] Contraseña del administrador definida por el equipo (nunca `Admin12345*`).
- [ ] `ENTORNO=produccion` y `CORS_ORIGINS` solo con el dominio real del frontend.
- [ ] `.env` no está en git (ya está en `.gitignore`); las claves se cargan en el panel del proveedor.
- [ ] HTTPS en el API y el frontend (los proveedores lo dan por defecto).
- [ ] `/health` en verde y login probado con el administrador.
- [ ] Probar un flujo completo: crear veterinario → login → propietario → mascota → cita → completar → historial.

## Riesgos conocidos (decisiones del equipo)
- El token de sesión vive en `localStorage` (vulnerable si hubiera XSS); aceptable para el alcance académico, mejorable con cookies `HttpOnly`.
- Redis gratuito suele tener límites de comandos/mes; el login usa pocos, pero conviene vigilarlo.
- Los servicios gratuitos "duermen" tras inactividad: la primera petición puede tardar.
- No hay copias de seguridad automáticas en el plan gratuito de la base de datos.
