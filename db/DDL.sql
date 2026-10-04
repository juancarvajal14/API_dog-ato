-- =====================================================================
-- DOG-ATO · Base de datos PostgreSQL (>= 13)
-- Menú, roles, perfiles y permisos (CRUD por módulo) gestionados desde la BD.
-- Script ÚNICO y COMPLETO (el único .sql del repositorio): deja a todo el equipo con la misma BD y los mismos datos.
-- De este archivo salen también el modelo ER (docs/modelo_er.md) y el script de la entrega.
--
-- Ejecutar con psql (no sirve la Query Tool de pgAdmin, usa comandos "\"):
--     psql -U postgres -f DDL.sql
-- En Windows, si psql no está en el PATH:
--     & "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -f DDL.sql
--
-- ¡OJO! Es un script de DESARROLLO: si la BD "dogato" ya existe, la BORRA y la
-- recrea desde cero (así todos quedan idénticos). No lo uses en producción.
-- Requisitos: PostgreSQL 13 o superior, y un usuario que pueda crear BD y la
-- extensión pgcrypto (p. ej. postgres).
--
-- Cuentas creadas (contraseñas de DESARROLLO, cámbienlas en producción):
--     admin@veterinaria.com        Admin12345*   (administrador)
--     andres.gomez@dogato.com      Vet12345*     (veterinario)
--     laura.martinez@dogato.com    Vet12345*     (veterinario)
--     diego.salazar@dogato.com     Vet12345*     (veterinario, INACTIVO)
-- Los datos de demostración están al final (sección DATOS DE DEMOSTRACIÓN).
-- =====================================================================

\set ON_ERROR_STOP on
\encoding UTF8

DROP DATABASE IF EXISTS dogato WITH (FORCE);
CREATE DATABASE dogato WITH ENCODING 'UTF8' TEMPLATE template0;
\connect dogato
-- \connect abre una conexión NUEVA: hay que fijar UTF8 otra vez (en Windows el cliente arranca en WIN1252 y dañaría las tildes)
\encoding UTF8

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ---------------------------------------------------------------------
-- CATÁLOGOS
-- ---------------------------------------------------------------------
CREATE TABLE tipo_documento (
    id_tipo_documento  INTEGER GENERATED ALWAYS AS IDENTITY,
    nombre             VARCHAR(50) NOT NULL,
    abreviacion        VARCHAR(5)  NOT NULL,
    CONSTRAINT pk_tipo_documento PRIMARY KEY (id_tipo_documento),
    CONSTRAINT uq_tipo_documento_abrev UNIQUE (abreviacion)
);

CREATE TABLE estado_cita (
    id_estado_cita  INTEGER GENERATED ALWAYS AS IDENTITY,
    nombre          VARCHAR(30) NOT NULL,
    CONSTRAINT pk_estado_cita PRIMARY KEY (id_estado_cita),
    CONSTRAINT uq_estado_cita_nombre UNIQUE (nombre)
);

-- ---------------------------------------------------------------------
-- SEGURIDAD: rol -> perfil -> (módulo, permiso)
-- ---------------------------------------------------------------------
CREATE TABLE rol (
    id_rol  INTEGER GENERATED ALWAYS AS IDENTITY,
    nombre  VARCHAR(50) NOT NULL,
    activo  BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT pk_rol PRIMARY KEY (id_rol),
    CONSTRAINT uq_rol_nombre UNIQUE (nombre)
);

CREATE TABLE perfil (
    id_perfil    INTEGER GENERATED ALWAYS AS IDENTITY,
    id_rol       INTEGER NOT NULL,
    nombre       VARCHAR(50) NOT NULL,
    descripcion  VARCHAR(500),
    activo       BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT pk_perfil PRIMARY KEY (id_perfil),
    CONSTRAINT uq_perfil_nombre UNIQUE (nombre),
    CONSTRAINT fk_perfil_rol FOREIGN KEY (id_rol) REFERENCES rol (id_rol)
);

-- Menú dinámico: sin ruta = carpeta que agrupa (solo 1 nivel); con ruta = opción que abre una pantalla.
-- "codigo" es la clave estable que usan el backend y el frontend (no el nombre visible).
CREATE TABLE modulo (
    id_modulo        INTEGER GENERATED ALWAYS AS IDENTITY,
    id_modulo_padre  INTEGER,
    codigo           VARCHAR(40) NOT NULL,
    nombre           VARCHAR(50) NOT NULL,
    descripcion      VARCHAR(500),
    ruta             VARCHAR(200),
    icono            VARCHAR(40),
    orden            INTEGER NOT NULL DEFAULT 1,
    activo           BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT pk_modulo PRIMARY KEY (id_modulo),
    CONSTRAINT uq_modulo_codigo UNIQUE (codigo),
    CONSTRAINT fk_modulo_padre FOREIGN KEY (id_modulo_padre) REFERENCES modulo (id_modulo),
    CONSTRAINT ck_modulo_no_self CHECK (id_modulo_padre IS NULL OR id_modulo_padre <> id_modulo)
);
CREATE UNIQUE INDEX uq_modulo_ruta ON modulo (ruta) WHERE ruta IS NOT NULL;

-- Acciones CRUD, cada una es un permiso independiente
CREATE TABLE permiso (
    id_permiso   INTEGER GENERATED ALWAYS AS IDENTITY,
    nombre       VARCHAR(30) NOT NULL,
    descripcion  VARCHAR(200),
    CONSTRAINT pk_permiso PRIMARY KEY (id_permiso),
    CONSTRAINT uq_permiso_nombre UNIQUE (nombre),
    CONSTRAINT ck_permiso_nombre CHECK (nombre = upper(nombre))
);

-- Lo que puede hacer cada perfil en cada opción de menú
CREATE TABLE perfil_modulo_permiso (
    id_perfil   INTEGER NOT NULL,
    id_modulo   INTEGER NOT NULL,
    id_permiso  INTEGER NOT NULL,
    CONSTRAINT pk_perfil_modulo_permiso PRIMARY KEY (id_perfil, id_modulo, id_permiso),
    CONSTRAINT fk_pmp_perfil  FOREIGN KEY (id_perfil)  REFERENCES perfil (id_perfil),
    CONSTRAINT fk_pmp_modulo  FOREIGN KEY (id_modulo)  REFERENCES modulo (id_modulo),
    CONSTRAINT fk_pmp_permiso FOREIGN KEY (id_permiso) REFERENCES permiso (id_permiso)
);

-- ---------------------------------------------------------------------
-- USUARIOS (administradores y veterinarios)
-- ---------------------------------------------------------------------
CREATE TABLE usuario (
    id_usuario         INTEGER GENERATED ALWAYS AS IDENTITY,
    id_tipo_documento  INTEGER NOT NULL,
    documento          VARCHAR(20)  NOT NULL,
    nombres            VARCHAR(100) NOT NULL,
    apellidos          VARCHAR(100) NOT NULL,
    email              VARCHAR(100) NOT NULL,
    telefono           VARCHAR(20),
    direccion          VARCHAR(200),
    contrasena_hash    VARCHAR(255) NOT NULL,   -- hash bcrypt, nunca texto plano
    activo             BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion     TIMESTAMP NOT NULL DEFAULT now(),
    CONSTRAINT pk_usuario PRIMARY KEY (id_usuario),
    CONSTRAINT uq_usuario_documento UNIQUE (id_tipo_documento, documento),
    CONSTRAINT fk_usuario_tipo_documento FOREIGN KEY (id_tipo_documento)
        REFERENCES tipo_documento (id_tipo_documento)
);
CREATE UNIQUE INDEX uq_usuario_email ON usuario (lower(email));

CREATE TABLE usuario_perfil (
    id_usuario  INTEGER NOT NULL,
    id_perfil   INTEGER NOT NULL,
    CONSTRAINT pk_usuario_perfil PRIMARY KEY (id_usuario, id_perfil),
    CONSTRAINT fk_usuario_perfil_usuario FOREIGN KEY (id_usuario) REFERENCES usuario (id_usuario),
    CONSTRAINT fk_usuario_perfil_perfil  FOREIGN KEY (id_perfil)  REFERENCES perfil (id_perfil)
);

-- Datos profesionales del veterinario; identidad y cuenta están en "usuario"
CREATE TABLE veterinario (
    id_veterinario        INTEGER GENERATED ALWAYS AS IDENTITY,
    id_usuario            INTEGER NOT NULL,
    especialidad          VARCHAR(100),
    registro_profesional  VARCHAR(30),
    CONSTRAINT pk_veterinario PRIMARY KEY (id_veterinario),
    CONSTRAINT uq_veterinario_usuario UNIQUE (id_usuario),
    CONSTRAINT uq_veterinario_registro UNIQUE (registro_profesional),
    CONSTRAINT fk_veterinario_usuario FOREIGN KEY (id_usuario) REFERENCES usuario (id_usuario)
);

-- ---------------------------------------------------------------------
-- NEGOCIO
-- ---------------------------------------------------------------------
-- Dueños de las mascotas (no tienen cuenta ni rol)
CREATE TABLE propietario (
    id_propietario     INTEGER GENERATED ALWAYS AS IDENTITY,
    id_tipo_documento  INTEGER NOT NULL,
    documento          VARCHAR(20)  NOT NULL,
    nombres            VARCHAR(100) NOT NULL,
    apellidos          VARCHAR(100) NOT NULL,
    telefono           VARCHAR(20),
    email              VARCHAR(100),
    direccion          VARCHAR(200),
    fecha_creacion     TIMESTAMP NOT NULL DEFAULT now(),
    CONSTRAINT pk_propietario PRIMARY KEY (id_propietario),
    CONSTRAINT uq_propietario_documento UNIQUE (id_tipo_documento, documento),
    CONSTRAINT fk_propietario_tipo_documento FOREIGN KEY (id_tipo_documento)
        REFERENCES tipo_documento (id_tipo_documento)
);

CREATE TABLE mascota (
    id_mascota        INTEGER GENERATED ALWAYS AS IDENTITY,
    id_propietario    INTEGER NOT NULL,
    nombre            VARCHAR(100) NOT NULL,
    especie           VARCHAR(50)  NOT NULL,
    raza              VARCHAR(50),
    sexo              VARCHAR(10) NOT NULL,
    fecha_nacimiento  DATE,
    CONSTRAINT pk_mascota PRIMARY KEY (id_mascota),
    CONSTRAINT fk_mascota_propietario FOREIGN KEY (id_propietario) REFERENCES propietario (id_propietario),
    CONSTRAINT ck_mascota_sexo CHECK (sexo IN ('macho', 'hembra'))
);

-- Toda cita queda asignada a un veterinario, aunque la cree un administrador
CREATE TABLE cita (
    id_cita          INTEGER GENERATED ALWAYS AS IDENTITY,
    id_mascota       INTEGER NOT NULL,
    id_veterinario   INTEGER NOT NULL,
    id_estado_cita   INTEGER NOT NULL,
    fecha_hora       TIMESTAMP NOT NULL,
    motivo_consulta  TEXT NOT NULL,
    CONSTRAINT pk_cita PRIMARY KEY (id_cita),
    CONSTRAINT fk_cita_mascota     FOREIGN KEY (id_mascota)     REFERENCES mascota (id_mascota),
    CONSTRAINT fk_cita_veterinario FOREIGN KEY (id_veterinario) REFERENCES veterinario (id_veterinario),
    CONSTRAINT fk_cita_estado_cita FOREIGN KEY (id_estado_cita) REFERENCES estado_cita (id_estado_cita)
);

-- Se registra al completar la cita (ver fn_completar_cita); es solo de consulta
CREATE TABLE historial_clinico (
    id_historial_clinico  INTEGER GENERATED ALWAYS AS IDENTITY,
    id_cita               INTEGER NOT NULL,
    fecha_registro        TIMESTAMP NOT NULL DEFAULT now(),
    diagnostico           TEXT,
    tratamiento           TEXT,
    observaciones         TEXT,
    CONSTRAINT pk_historial_clinico PRIMARY KEY (id_historial_clinico),
    CONSTRAINT uq_historial_cita UNIQUE (id_cita),
    CONSTRAINT fk_historial_cita FOREIGN KEY (id_cita) REFERENCES cita (id_cita)
);

-- ---------------------------------------------------------------------
-- ÍNDICES sobre llaves foráneas (PostgreSQL no los crea solo)
-- ---------------------------------------------------------------------
CREATE INDEX ix_perfil_rol            ON perfil (id_rol);
CREATE INDEX ix_modulo_padre          ON modulo (id_modulo_padre);
CREATE INDEX ix_usuario_perfil_perfil ON usuario_perfil (id_perfil);
CREATE INDEX ix_pmp_modulo            ON perfil_modulo_permiso (id_modulo);
CREATE INDEX ix_pmp_permiso           ON perfil_modulo_permiso (id_permiso);
CREATE INDEX ix_mascota_propietario   ON mascota (id_propietario);
CREATE INDEX ix_cita_mascota          ON cita (id_mascota);
CREATE INDEX ix_cita_vet_fecha        ON cita (id_veterinario, fecha_hora);
CREATE INDEX ix_cita_estado           ON cita (id_estado_cita);

-- ---------------------------------------------------------------------
-- REGLAS DE INTEGRIDAD (triggers)
-- ---------------------------------------------------------------------

-- El menú tiene 2 niveles: carpeta (sin ruta, sin padre) -> opción (con ruta)
CREATE FUNCTION fn_modulo_valida() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    v_padre modulo%ROWTYPE;
BEGIN
    IF NEW.id_modulo_padre IS NOT NULL THEN
        SELECT * INTO v_padre FROM modulo WHERE id_modulo = NEW.id_modulo_padre;
        IF v_padre.ruta IS NOT NULL OR v_padre.id_modulo_padre IS NOT NULL THEN
            RAISE EXCEPTION 'El módulo padre debe ser una carpeta de primer nivel (sin ruta)';
        END IF;
        IF NEW.ruta IS NULL THEN
            RAISE EXCEPTION 'Una opción dentro de una carpeta debe tener ruta';
        END IF;
    END IF;
    IF TG_OP = 'UPDATE' AND NEW.ruta IS NOT NULL
       AND EXISTS (SELECT 1 FROM modulo WHERE id_modulo_padre = NEW.id_modulo) THEN
        RAISE EXCEPTION 'Una carpeta con opciones no puede tener ruta';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER trg_modulo_valida BEFORE INSERT OR UPDATE ON modulo
    FOR EACH ROW EXECUTE FUNCTION fn_modulo_valida();

-- Los permisos se asignan solo a opciones (con ruta); las carpetas se muestran
-- automáticamente si el usuario puede ver al menos una de sus opciones.
CREATE FUNCTION fn_pmp_valida() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM modulo WHERE id_modulo = NEW.id_modulo AND ruta IS NULL) THEN
        RAISE EXCEPTION 'No se asignan permisos a carpetas, solo a opciones con ruta';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER trg_pmp_valida BEFORE INSERT OR UPDATE ON perfil_modulo_permiso
    FOR EACH ROW EXECUTE FUNCTION fn_pmp_valida();

-- Una cita nueva solo se asigna a un veterinario activo; completada/cancelada son estados finales
CREATE FUNCTION fn_cita_valida() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    v_estado_viejo VARCHAR(30);
BEGIN
    IF TG_OP = 'INSERT' THEN
        IF NOT EXISTS (SELECT 1 FROM veterinario v JOIN usuario u USING (id_usuario)
                       WHERE v.id_veterinario = NEW.id_veterinario AND u.activo) THEN
            RAISE EXCEPTION 'El veterinario está inactivo y no puede recibir citas';
        END IF;
    ELSE
        SELECT nombre INTO v_estado_viejo FROM estado_cita WHERE id_estado_cita = OLD.id_estado_cita;
        IF v_estado_viejo <> 'pendiente' THEN
            IF NEW.id_estado_cita <> OLD.id_estado_cita OR NEW.id_veterinario <> OLD.id_veterinario
               OR NEW.fecha_hora <> OLD.fecha_hora OR NEW.id_mascota <> OLD.id_mascota THEN
                RAISE EXCEPTION 'Una cita % no se puede modificar', v_estado_viejo;
            END IF;
        END IF;
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER trg_cita_valida BEFORE INSERT OR UPDATE ON cita
    FOR EACH ROW EXECUTE FUNCTION fn_cita_valida();

-- El historial solo existe para citas completadas y no se edita ni se borra
CREATE FUNCTION fn_historial_valida() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        IF NOT EXISTS (SELECT 1 FROM cita c JOIN estado_cita e USING (id_estado_cita)
                       WHERE c.id_cita = NEW.id_cita AND e.nombre = 'completada') THEN
            RAISE EXCEPTION 'Solo se registra historial para citas completadas (use fn_completar_cita)';
        END IF;
        RETURN NEW;
    END IF;
    RAISE EXCEPTION 'El historial clínico es de solo consulta';
END $$;
CREATE TRIGGER trg_historial_valida BEFORE INSERT OR UPDATE OR DELETE ON historial_clinico
    FOR EACH ROW EXECUTE FUNCTION fn_historial_valida();

-- ---------------------------------------------------------------------
-- FUNCIONES PARA EL BACKEND (autorización y menú viven en la BD)
-- ---------------------------------------------------------------------

-- Pares (módulo, permiso) vigentes de un usuario: usuario, perfil, rol y módulo deben estar activos
CREATE FUNCTION fn_permisos_usuario(p_id_usuario INTEGER)
RETURNS TABLE (id_modulo INTEGER, permiso VARCHAR)
LANGUAGE sql STABLE AS $$
    SELECT DISTINCT pmp.id_modulo, pe.nombre
    FROM usuario u
    JOIN usuario_perfil up ON up.id_usuario = u.id_usuario
    JOIN perfil p ON p.id_perfil = up.id_perfil AND p.activo
    JOIN rol r ON r.id_rol = p.id_rol AND r.activo
    JOIN perfil_modulo_permiso pmp ON pmp.id_perfil = p.id_perfil
    JOIN modulo m ON m.id_modulo = pmp.id_modulo AND m.activo
    JOIN permiso pe ON pe.id_permiso = pmp.id_permiso
    WHERE u.id_usuario = p_id_usuario AND u.activo
$$;

-- Menú del usuario: opciones donde tiene LEER + las carpetas que las contienen.
-- El backend arma el árbol con id_modulo_padre y ordena por "orden".
CREATE FUNCTION fn_menu_usuario(p_id_usuario INTEGER)
RETURNS TABLE (id_modulo INTEGER, id_modulo_padre INTEGER, codigo VARCHAR, nombre VARCHAR,
               ruta VARCHAR, icono VARCHAR, orden INTEGER, permisos VARCHAR[])
LANGUAGE sql STABLE AS $$
    WITH perm AS (
        SELECT fp.id_modulo, array_agg(fp.permiso ORDER BY fp.permiso) AS permisos
        FROM fn_permisos_usuario(p_id_usuario) fp
        GROUP BY fp.id_modulo
    ),
    hojas AS (
        SELECT m.id_modulo, m.id_modulo_padre, m.codigo, m.nombre, m.ruta, m.icono, m.orden, perm.permisos
        FROM modulo m
        JOIN perm ON perm.id_modulo = m.id_modulo
        WHERE m.ruta IS NOT NULL AND m.activo AND 'LEER' = ANY (perm.permisos)
          AND (m.id_modulo_padre IS NULL
               OR EXISTS (SELECT 1 FROM modulo pa WHERE pa.id_modulo = m.id_modulo_padre AND pa.activo))
    )
    SELECT * FROM hojas
    UNION ALL
    SELECT f.id_modulo, NULL, f.codigo, f.nombre, NULL, f.icono, f.orden, ARRAY[]::VARCHAR[]
    FROM modulo f
    WHERE f.ruta IS NULL AND f.activo
      AND EXISTS (SELECT 1 FROM hojas h WHERE h.id_modulo_padre = f.id_modulo)
    ORDER BY orden
$$;

-- ¿Puede el usuario ejecutar el permiso (CREAR/LEER/ACTUALIZAR/ELIMINAR) en el módulo?
CREATE FUNCTION fn_tiene_permiso(p_id_usuario INTEGER, p_codigo_modulo VARCHAR, p_permiso VARCHAR)
RETURNS BOOLEAN LANGUAGE sql STABLE AS $$
    SELECT EXISTS (
        SELECT 1
        FROM fn_permisos_usuario(p_id_usuario) fp
        JOIN modulo m ON m.id_modulo = fp.id_modulo
        WHERE m.codigo = p_codigo_modulo AND fp.permiso = upper(p_permiso)
    )
$$;

-- Matriz perfil x módulo x permiso (pantalla "Módulos y permisos")
CREATE VIEW v_matriz_permisos AS
SELECT r.nombre AS rol, p.id_perfil, p.nombre AS perfil, m.id_modulo, m.codigo AS modulo_codigo,
       m.nombre AS modulo, pe.nombre AS permiso
FROM perfil_modulo_permiso pmp
JOIN perfil p   ON p.id_perfil = pmp.id_perfil
JOIN rol r      ON r.id_rol = p.id_rol
JOIN modulo m   ON m.id_modulo = pmp.id_modulo
JOIN permiso pe ON pe.id_permiso = pmp.id_permiso;

-- Alta atómica de veterinario: usuario + perfil + datos profesionales.
-- El backend envía la contraseña YA hasheada (bcrypt).
CREATE FUNCTION fn_crear_veterinario(
    p_id_tipo_documento INTEGER, p_documento VARCHAR, p_nombres VARCHAR, p_apellidos VARCHAR,
    p_email VARCHAR, p_telefono VARCHAR, p_direccion VARCHAR, p_contrasena_hash VARCHAR,
    p_especialidad VARCHAR, p_registro_profesional VARCHAR, p_id_perfil INTEGER
) RETURNS INTEGER LANGUAGE plpgsql AS $$
DECLARE
    v_id_usuario INTEGER;
    v_id_veterinario INTEGER;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM perfil p JOIN rol r USING (id_rol)
                   WHERE p.id_perfil = p_id_perfil AND r.nombre = 'Veterinario') THEN
        RAISE EXCEPTION 'El perfil indicado no pertenece al rol Veterinario';
    END IF;

    INSERT INTO usuario (id_tipo_documento, documento, nombres, apellidos, email, telefono, direccion, contrasena_hash)
    VALUES (p_id_tipo_documento, p_documento, p_nombres, p_apellidos, p_email, p_telefono, p_direccion, p_contrasena_hash)
    RETURNING id_usuario INTO v_id_usuario;

    INSERT INTO usuario_perfil (id_usuario, id_perfil) VALUES (v_id_usuario, p_id_perfil);

    INSERT INTO veterinario (id_usuario, especialidad, registro_profesional)
    VALUES (v_id_usuario, p_especialidad, p_registro_profesional)
    RETURNING id_veterinario INTO v_id_veterinario;

    RETURN v_id_veterinario;
END $$;

-- Completar cita + registrar historial en una sola transacción
CREATE FUNCTION fn_completar_cita(p_id_cita INTEGER, p_diagnostico TEXT, p_tratamiento TEXT, p_observaciones TEXT)
RETURNS INTEGER LANGUAGE plpgsql AS $$
DECLARE
    v_estado VARCHAR(30);
    v_id_historial INTEGER;
BEGIN
    SELECT e.nombre INTO v_estado
    FROM cita c JOIN estado_cita e USING (id_estado_cita)
    WHERE c.id_cita = p_id_cita
    FOR UPDATE OF c;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'La cita % no existe', p_id_cita;
    END IF;
    IF v_estado <> 'pendiente' THEN
        RAISE EXCEPTION 'Solo se pueden completar citas pendientes (estado actual: %)', v_estado;
    END IF;

    UPDATE cita SET id_estado_cita = (SELECT id_estado_cita FROM estado_cita WHERE nombre = 'completada')
    WHERE id_cita = p_id_cita;

    INSERT INTO historial_clinico (id_cita, diagnostico, tratamiento, observaciones)
    VALUES (p_id_cita, p_diagnostico, p_tratamiento, p_observaciones)
    RETURNING id_historial_clinico INTO v_id_historial;

    RETURN v_id_historial;
END $$;

-- ---------------------------------------------------------------------
-- DATOS INICIALES
-- ---------------------------------------------------------------------
INSERT INTO tipo_documento (nombre, abreviacion) VALUES
    ('Cédula de ciudadanía', 'CC'),
    ('Tarjeta de identidad', 'TI'),
    ('Cédula de extranjería', 'CE'),
    ('Pasaporte', 'PA');

INSERT INTO estado_cita (nombre) VALUES ('pendiente'), ('completada'), ('cancelada');

INSERT INTO rol (nombre) VALUES ('Administrador'), ('Veterinario');

INSERT INTO perfil (id_rol, nombre, descripcion)
SELECT id_rol, 'Administrador del sistema',
       'Gestiona veterinarios, propietarios, mascotas, citas y registra diagnósticos'
FROM rol WHERE nombre = 'Administrador';
INSERT INTO perfil (id_rol, nombre, descripcion)
SELECT id_rol, 'Médico veterinario',
       'Gestiona propietarios, mascotas, citas y registra diagnósticos'
FROM rol WHERE nombre = 'Veterinario';

INSERT INTO permiso (nombre, descripcion) VALUES
    ('CREAR',      'Crear registros'),
    ('LEER',       'Consultar registros'),
    ('ACTUALIZAR', 'Modificar registros (incluye activar/desactivar y completar/cancelar citas)'),
    ('ELIMINAR',   'Eliminar registros (no asignado a ningún perfil por ahora)');

-- Menú: carpetas
INSERT INTO modulo (codigo, nombre, descripcion, icono, orden) VALUES
    ('SEGURIDAD',      'Seguridad',       'Administración de acceso',       'shield',  1),
    ('GESTION_CLINICA','Gestión clínica', 'Operación de la veterinaria',    'heart-pulse', 2);

-- Menú: opciones
INSERT INTO modulo (id_modulo_padre, codigo, nombre, ruta, icono, orden)
SELECT p.id_modulo, v.codigo, v.nombre, v.ruta, v.icono, v.orden
FROM (VALUES
    ('SEGURIDAD',       'SEG_VETERINARIOS', 'Veterinarios',        '/seguridad/veterinarios', 'stethoscope', 1),
    ('SEGURIDAD',       'SEG_ROLES',        'Roles',               '/seguridad/roles',        'user-cog',    2),
    ('SEGURIDAD',       'SEG_PERFILES',     'Perfiles',            '/seguridad/perfiles',     'id-card',     3),
    ('SEGURIDAD',       'SEG_MODULOS',      'Módulos y permisos',  '/seguridad/modulos',      'key-round',   4),
    ('GESTION_CLINICA', 'CLI_PROPIETARIOS', 'Propietarios',        '/clinica/propietarios',   'users',       1),
    ('GESTION_CLINICA', 'CLI_MASCOTAS',     'Mascotas',            '/clinica/mascotas',       'paw-print',   2),
    ('GESTION_CLINICA', 'CLI_CITAS',        'Citas',               '/clinica/citas',          'calendar-clock', 3),
    ('GESTION_CLINICA', 'CLI_HISTORIAL',    'Historial clínico',   '/clinica/historial',      'clipboard-list', 4)
) AS v(padre, codigo, nombre, ruta, icono, orden)
JOIN modulo p ON p.codigo = v.padre;

-- Matriz de permisos. Historial clínico: solo LEER (se escribe al completar una cita).
INSERT INTO perfil_modulo_permiso (id_perfil, id_modulo, id_permiso)
SELECT p.id_perfil, m.id_modulo, pe.id_permiso
FROM (VALUES
    ('Administrador del sistema', 'SEG_VETERINARIOS', ARRAY['CREAR','LEER','ACTUALIZAR']),
    ('Administrador del sistema', 'SEG_ROLES',        ARRAY['CREAR','LEER','ACTUALIZAR']),
    ('Administrador del sistema', 'SEG_PERFILES',     ARRAY['CREAR','LEER','ACTUALIZAR']),
    ('Administrador del sistema', 'SEG_MODULOS',      ARRAY['CREAR','LEER','ACTUALIZAR']),
    ('Administrador del sistema', 'CLI_PROPIETARIOS', ARRAY['CREAR','LEER','ACTUALIZAR']),
    ('Administrador del sistema', 'CLI_MASCOTAS',     ARRAY['CREAR','LEER','ACTUALIZAR']),
    ('Administrador del sistema', 'CLI_CITAS',        ARRAY['CREAR','LEER','ACTUALIZAR']),
    ('Administrador del sistema', 'CLI_HISTORIAL',    ARRAY['LEER']),
    ('Médico veterinario',        'CLI_PROPIETARIOS', ARRAY['CREAR','LEER','ACTUALIZAR']),
    ('Médico veterinario',        'CLI_MASCOTAS',     ARRAY['CREAR','LEER','ACTUALIZAR']),
    ('Médico veterinario',        'CLI_CITAS',        ARRAY['CREAR','LEER','ACTUALIZAR']),
    ('Médico veterinario',        'CLI_HISTORIAL',    ARRAY['LEER'])
) AS v(perfil, modulo, permisos)
JOIN perfil p ON p.nombre = v.perfil
JOIN modulo m ON m.codigo = v.modulo
CROSS JOIN LATERAL unnest(v.permisos) AS x(permiso)
JOIN permiso pe ON pe.nombre = x.permiso;

-- Administrador inicial · correo: admin@veterinaria.com · contraseña: Admin12345*
-- (cámbiala tras el primer ingreso; el hash bcrypt lo genera pgcrypto)
INSERT INTO usuario (id_tipo_documento, documento, nombres, apellidos, email, telefono, contrasena_hash)
SELECT id_tipo_documento, '1000000000', 'Admin', 'del sistema', 'admin@veterinaria.com',
       '3105324587', crypt('Admin12345*', gen_salt('bf', 10))
FROM tipo_documento WHERE abreviacion = 'CC';

INSERT INTO usuario_perfil (id_usuario, id_perfil)
SELECT u.id_usuario, p.id_perfil
FROM usuario u, perfil p
WHERE u.email = 'admin@veterinaria.com' AND p.nombre = 'Administrador del sistema';

-- ---------------------------------------------------------------------
-- DATOS DE DEMOSTRACIÓN (los mismos del mockup del frontend)
-- Se pueden borrar esta sección completa sin afectar la estructura ni la seguridad.
-- Los IDs se asumen consecutivos porque la BD se crea siempre desde cero.
-- ---------------------------------------------------------------------

-- Veterinarios (contraseña: Vet12345*)
SELECT fn_crear_veterinario(1, '1122334455', 'Andrés', 'Gómez', 'andres.gomez@dogato.com', '3012345678',
           'Calle 30 #65-10, Medellín', crypt('Vet12345*', gen_salt('bf', 10)), 'Medicina general', 'MV-0001',
           (SELECT id_perfil FROM perfil WHERE nombre = 'Médico veterinario'));
SELECT fn_crear_veterinario(1, '1099887766', 'Laura', 'Martínez', 'laura.martinez@dogato.com', '3023456789',
           'Cra 70 #44-20, Medellín', crypt('Vet12345*', gen_salt('bf', 10)), 'Dermatología', 'MV-0002',
           (SELECT id_perfil FROM perfil WHERE nombre = 'Médico veterinario'));
SELECT fn_crear_veterinario(1, '1055667788', 'Diego', 'Salazar', 'diego.salazar@dogato.com', '3034567890',
           'Calle 12 Sur #28-40, Envigado', crypt('Vet12345*', gen_salt('bf', 10)), 'Cirugía', 'MV-0003',
           (SELECT id_perfil FROM perfil WHERE nombre = 'Médico veterinario'));
UPDATE usuario SET activo = FALSE WHERE email = 'diego.salazar@dogato.com';

-- Propietarios (todos con cédula de ciudadanía, id_tipo_documento = 1)
INSERT INTO propietario (id_tipo_documento, documento, nombres, apellidos, telefono, email, direccion) VALUES
    (1, '43267891',   'Mariana',    'Ortiz',    '3101112233', 'mariana.ortiz@gmail.com',    'Cra 25 #33-12, Medellín'),
    (1, '71234567',   'Felipe',     'Vargas',   '3112223344', 'felipe.vargas@gmail.com',    'Calle 50 #20-30, Itagüí'),
    (1, '1035678912', 'Daniela',    'Cardona',  '3123334455', 'daniela.cardona@gmail.com',  'Cra 80 #12-05, Medellín'),
    (1, '98765432',   'Santiago',   'Zuluaga',  '3134445566', 'santiago.zuluaga@gmail.com', 'Calle 44 #70-18, Medellín'),
    (1, '1128976543', 'Valentina',  'Ríos',     '3145556677', 'valentina.rios@gmail.com',   'Cra 15 #8-90, Sabaneta'),
    (1, '79456123',   'Juan Pablo', 'Correa',   '3156667788', 'juanpablo.correa@gmail.com', 'Calle 33 #76-40, Medellín');

INSERT INTO mascota (id_propietario, nombre, especie, raza, sexo, fecha_nacimiento) VALUES
    (1, 'Rocco', 'Perro',  'Labrador',              'macho',  '2021-04-12'),
    (1, 'Luna',  'Gato',   'Siamés',                'hembra', '2022-08-03'),
    (2, 'Max',   'Perro',  'Bulldog Francés',       'macho',  '2020-01-22'),
    (3, 'Nala',  'Gato',   'Común Europeo',         'hembra', '2023-02-14'),
    (3, 'Toby',  'Perro',  'Beagle',                'macho',  '2019-11-30'),
    (4, 'Coco',  'Conejo', 'Holandés',              'hembra', '2023-06-10'),
    (5, 'Simón', 'Perro',  'Golden Retriever',      'macho',  '2022-03-05'),
    (5, 'Mia',   'Gato',   'Persa',                 'hembra', '2021-09-18'),
    (6, 'Zeus',  'Perro',  'Pastor Alemán',         'macho',  '2020-07-25'),
    (6, 'Kiwi',  'Ave',    'Periquito Australiano', 'hembra', '2023-10-01');

-- Citas: estados 1 = pendiente, 2 = completada, 3 = cancelada. Veterinarios: 1 = Andrés, 2 = Laura.
INSERT INTO cita (id_mascota, id_veterinario, id_estado_cita, fecha_hora, motivo_consulta) VALUES
    (1,  1, 2, '2026-08-20 09:00', 'Vacunación anual'),
    (3,  2, 2, '2026-08-22 11:30', 'Revisión de piel, se observa enrojecimiento'),
    (5,  1, 2, '2026-08-25 15:00', 'Chequeo general de rutina'),
    (7,  2, 3, '2026-08-28 10:00', 'Cojera en pata trasera derecha'),
    (9,  1, 2, '2026-09-01 08:30', 'Control post-operatorio'),
    (2,  2, 1, '2026-09-10 14:00', 'Baja de apetito hace 3 días'),
    (4,  1, 1, '2026-09-11 09:30', 'Primera consulta y esquema de vacunas'),
    (8,  2, 1, '2026-09-12 16:00', 'Control de peso'),
    (6,  1, 1, '2026-09-13 10:00', 'Revisión dental'),
    (10, 2, 1, '2026-09-15 11:00', 'Chequeo general');

-- Historial de las citas completadas (id_cita 1, 2, 3 y 5)
INSERT INTO historial_clinico (id_cita, fecha_registro, diagnostico, tratamiento, observaciones) VALUES
    (1, '2026-08-20 09:40', 'Paciente sano, sin hallazgos relevantes',
        'Aplicación de refuerzo de vacuna polivalente',
        'Volver a vacunar en 12 meses. Se recomienda mantener desparasitación trimestral'),
    (2, '2026-08-22 12:05', 'Dermatitis alérgica leve, posible reacción a alimento',
        'Shampoo medicado cada 3 días por 2 semanas, antihistamínico oral',
        'Evaluar cambio de dieta si no hay mejoría en 15 días'),
    (3, '2026-08-25 15:25', 'Sin alteraciones, signos vitales normales',
        'No requiere tratamiento',
        'Continuar con controles semestrales'),
    (5, '2026-09-01 09:00', 'Cicatrización adecuada de herida quirúrgica',
        'Retiro de puntos, limpieza de la zona',
        'Evitar actividad física intensa por 5 días más');

COMMIT;
