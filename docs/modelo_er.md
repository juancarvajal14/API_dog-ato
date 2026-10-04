# Modelo entidad–relación de DOG-ATO

Generado a partir de la base de datos creada con `db/DDL.sql` (única fuente del modelo). Imagen lista para el documento:
[`modelo_er.png`](modelo_er.png) · texto editable del diagrama: [`modelo_er.mmd`](modelo_er.mmd) (Mermaid).

![Modelo ER de DOG-ATO](modelo_er.png)

## Cómo leerlo
- **PK** llave primaria · **FK** llave foránea · **UK** valor único · «opcional» = admite NULL.
- `||--o{` uno a muchos · `||--|o` uno a uno (como mucho). Todas las llaves primarias son `GENERATED ALWAYS AS IDENTITY`.
- Reglas que el diagrama no muestra y que viven en la BD: correo único sin distinguir mayúsculas, ruta de módulo única, y los triggers
  del menú (2 niveles), de las citas (estados finales, veterinario activo) y del historial (solo lectura, solo de citas completadas).

## Grupos de tablas
| Grupo | Tablas | Para qué |
|---|---|---|
| Catálogos | `tipo_documento`, `estado_cita` | valores repetibles fuera de las tablas de negocio (3FN) |
| Seguridad (gestionada desde la BD) | `rol`, `perfil`, `modulo`, `permiso`, `perfil_modulo_permiso`, `usuario_perfil` | quién entra, qué menú ve y qué puede hacer (CRUD por módulo) |
| Personas | `usuario`, `veterinario`, `propietario` | cuentas del sistema, datos profesionales (1:1 con usuario) y dueños de mascotas (sin cuenta) |
| Operación clínica | `mascota`, `cita`, `historial_clinico` | pacientes, atenciones y su registro (1:1 con la cita) |

## Normalización (3FN)
- **1FN:** campos atómicos (tipo y número de documento, nombres y apellidos separados); sin listas ni grupos repetidos.
- **2FN:** las tablas de llave compuesta (`usuario_perfil`, `perfil_modulo_permiso`) solo contienen la llave: ningún atributo depende de una parte de ella.
- **3FN:** sin dependencias transitivas: el estado de la cita y el tipo de documento son catálogos referenciados; la identidad vive en `usuario` y
  los datos profesionales en `veterinario`; el permiso se asigna a (perfil, módulo, permiso) y no se repite texto.

## Diagrama (Mermaid)
```mermaid
erDiagram
  estado_cita ||--o{ cita : "esta_en"
  mascota ||--o{ cita : "tiene"
  veterinario ||--o{ cita : "atiende"
  cita ||--|o historial_clinico : "registra"
  propietario ||--o{ mascota : "posee"
  modulo ||--o{ modulo : "contiene"
  rol ||--o{ perfil : "agrupa"
  modulo ||--o{ perfil_modulo_permiso : "sobre"
  perfil ||--o{ perfil_modulo_permiso : "define"
  permiso ||--o{ perfil_modulo_permiso : "otorga"
  tipo_documento ||--o{ propietario : "identifica"
  tipo_documento ||--o{ usuario : "identifica"
  perfil ||--o{ usuario_perfil : "tiene"
  usuario ||--o{ usuario_perfil : "tiene"
  usuario ||--|o veterinario : "es"
  tipo_documento {
    int id_tipo_documento PK
    string nombre
    string abreviacion UK
  }
  estado_cita {
    int id_estado_cita PK
    string nombre UK
  }
  rol {
    int id_rol PK
    string nombre UK
    bool activo
  }
  perfil {
    int id_perfil PK
    int id_rol FK
    string nombre UK
    string descripcion  "opcional"
    bool activo
  }
  modulo {
    int id_modulo PK
    int id_modulo_padre FK "opcional"
    string codigo UK
    string nombre
    string descripcion  "opcional"
    string ruta  "opcional"
    string icono  "opcional"
    int orden
    bool activo
  }
  permiso {
    int id_permiso PK
    string nombre UK
    string descripcion  "opcional"
  }
  perfil_modulo_permiso {
    int id_perfil PK,FK
    int id_modulo PK,FK
    int id_permiso PK,FK
  }
  usuario {
    int id_usuario PK
    int id_tipo_documento FK
    string documento
    string nombres
    string apellidos
    string email
    string telefono  "opcional"
    string direccion  "opcional"
    string contrasena_hash
    bool activo
    timestamp fecha_creacion
  }
  usuario_perfil {
    int id_usuario PK,FK
    int id_perfil PK,FK
  }
  veterinario {
    int id_veterinario PK
    int id_usuario FK
    string especialidad  "opcional"
    string registro_profesional  "opcional"
  }
  propietario {
    int id_propietario PK
    int id_tipo_documento FK
    string documento
    string nombres
    string apellidos
    string telefono  "opcional"
    string email  "opcional"
    string direccion  "opcional"
    timestamp fecha_creacion
  }
  mascota {
    int id_mascota PK
    int id_propietario FK
    string nombre
    string especie
    string raza  "opcional"
    string sexo
    date fecha_nacimiento  "opcional"
  }
  cita {
    int id_cita PK
    int id_mascota FK
    int id_veterinario FK
    int id_estado_cita FK
    timestamp fecha_hora
    text motivo_consulta
  }
  historial_clinico {
    int id_historial_clinico PK
    int id_cita FK
    timestamp fecha_registro
    text diagnostico  "opcional"
    text tratamiento  "opcional"
    text observaciones  "opcional"
  }
```

## Cómo volver a generarlo
1. Ejecutar `db/DDL.sql` (o usar la BD `dogato` ya creada).
2. En pgAdmin: clic derecho en la base → **ERD For Database** (diagrama equivalente generado por la propia herramienta), o pegar el bloque
   Mermaid de arriba en https://mermaid.live para exportarlo como imagen.
