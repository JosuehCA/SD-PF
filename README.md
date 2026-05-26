# Sistema Distribuido de Citas Médicas

## Integrantes del equipo

* Cabrera Alcocer Herberth Josueh

* Canto Paredes Rodrigo Adrián

* Ceballos Pérez Andrea

* Dzul López Alex Enrique

* Kuh Esquivel Mauro Arif


## Documentación Técnica

---

## Tabla de Contenidos

1. [Arquitectura del Sistema](#1-arquitectura-del-sistema)
2. [Diseño de Base de Datos](#2-diseño-de-base-de-datos)
3. [Especificación de Servicios Web / API](#3-especificación-de-servicios-web--api)
4. [Descripción de la Interfaz de Usuario](#4-descripción-de-la-interfaz-de-usuario)
5. [Control de Concurrencia](#5-control-de-concurrencia)
6. [Mecanismos de Seguridad](#6-mecanismos-de-seguridad)
7. [Configuración y Despliegue](#7-configuración-y-despliegue)

---

## 1. Arquitectura del Sistema

### 1.1 Arquitectura de Tres Capas

El sistema implementa una **arquitectura distribuida de tres capas** que separa las responsabilidades en componentes independientes y comunicables entre sí.

```
┌─────────────────────────────────────────────────────────────────┐
│                    CAPA DE PRESENTACIÓN                          │
│          (Templates HTML + CSS + JavaScript)                     │
│                                                                  │
│  VistaLogin │ VistaDashboard │ VistaCitas │ VistaHistorial │...  │
└──────────────────────────────┬──────────────────────────────────┘
                               │ HTTP (puerto 8000)
┌──────────────────────────────▼──────────────────────────────────┐
│                    CAPA DE LÓGICA DE NEGOCIO                     │
│                                                                  │
│  ┌─────────────────────┐        ┌────────────────────────────┐  │
│  │   Django (puerto     │  HTTP  │  Flask Token Server        │  │
│  │   8000)              │◄──────►│  (puerto 5001)             │  │
│  │                      │        │                            │  │
│  │  • Autenticación     │        │  • Exclusión mutua         │  │
│  │  • CRUD Pacientes    │        │  • Control de tokens       │  │
│  │  • Gestión de Citas  │        │  • TTL auto-expiración     │  │
│  │  • Historial Clínico │        │  • Autenticación interna   │  │
│  │  • Reportes          │        │                            │  │
│  │  • Auditoría         │        └────────────────────────────┘  │
│  └──────────┬───────────┘                                        │
└─────────────┼────────────────────────────────────────────────────┘
              │
┌─────────────▼────────────────────────────────────────────────────┐
│                       CAPA DE DATOS                               │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │                    SQLite Database                          │   │
│  │                                                            │   │
│  │  Usuario │ Paciente │ Cita │ Consulta │ Historial │ Audit  │   │
│  │                                                            │   │
│  │  * Datos clínicos almacenados con cifrado AES-256         │   │
│  │  * Contraseñas hasheadas con PBKDF2-SHA256                │   │
│  └───────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────┘
```

### 1.2 Componentes del Sistema

| Componente | Tecnología | Puerto | Responsabilidad |
|-----------|-----------|--------|-----------------|
| Servidor Web Principal | Django 6.0.5 | 8000 | Lógica de negocio, autenticación, renderizado de vistas |
| Servidor de Tokens | Flask 3.1.3 | 5001 | Exclusión mutua distribuida para agendado de citas |
| Base de Datos | SQLite3 | — | Persistencia de datos con cifrado en reposo |
| Frontend | HTML5 + CSS3 + JS | — | Interfaz de usuario responsiva |

### 1.3 Flujo de Datos

#### Flujo de Agendado de Cita (con exclusión mutua):

```
Usuario ──► Django ──► Flask (solicitar_token)
                          │
                          ├── 409: Slot ocupado → mensaje de error
                          │
                          └── 200: Token concedido
                                    │
                          Django ◄───┘
                            │
                            ├── transaction.atomic() → INSERT cita
                            │
                            └── Flask (liberar_token) → Slot liberado
```

#### Flujo de Datos Clínicos (con cifrado):

```
Formulario (texto plano) ──► Vista Django ──► EncryptedField.get_prep_value()
                                                       │
                                              encrypt(AES-256) ──► Base de Datos
                                                                   (cifrado)

Base de Datos (cifrado) ──► EncryptedField.from_db_value() ──► decrypt()
                                                                    │
                                                     Template (texto plano) ◄─┘
```

---

## 2. Diseño de Base de Datos

### 2.1 Diagrama Entidad-Relación

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│   Usuario    │       │   Paciente   │       │     Cita     │
├──────────────┤       ├──────────────┤       ├──────────────┤
│ id (PK)      │1     1│ id (PK)      │1     *│ id (PK)      │
│ username     │───────│ usuario (FK)  │───────│ paciente(FK) │
│ password     │       │ nombre        │       │ fecha        │
│ email        │       │ direccion     │       │ hora         │
│ rol          │       │ correo        │       │ estado       │
│ is_staff     │       │ telefono      │       └──────┬───────┘
│ is_superuser │       │ edad          │              │ 1
└──────────────┘       │ sexo          │              │
                       └──────────────┘       ┌──────▼───────┐
                                              │   Consulta   │
┌──────────────┐                              ├──────────────┤
│   AuditLog   │                              │ id (PK)      │
├──────────────┤                              │ cita (FK) 🔑 │
│ id (PK)      │                              │ temperatura🔒│
│ usuario (FK) │                              │ peso 🔒      │
│ accion       │                              │ altura 🔒    │
│ modelo       │                              │ presion 🔒   │
│ objeto_id    │                              │ fecha_reg    │
│ descripcion  │                              └──────┬───────┘
│ fecha        │                                     │ 1
│ ip           │                              ┌──────▼───────┐
└──────────────┘                              │  Historial   │
                                              ├──────────────┤
                                              │ id (PK)      │
                                              │ consulta(FK) │
                                              │ diagnostico🔒│
                                              │ resultados 🔒│
                                              │ prescripc. 🔒│
                                              └──────────────┘

🔒 = Campo cifrado (AES-256)
🔑 = Relación OneToOne
```

### 2.2 Descripción de Entidades

#### Usuario (AbstractUser de Django)
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | BigAutoField (PK) | Identificador único |
| username | CharField(150) | Nombre de usuario para login |
| password | CharField(128) | Contraseña hasheada (PBKDF2-SHA256) |
| email | EmailField | Correo electrónico |
| rol | CharField(20) | "MEDICO" o "PACIENTE" |
| is_staff | BooleanField | Indica si es administrador |

#### Paciente
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | BigAutoField (PK) | Identificador único |
| usuario | OneToOneField → Usuario | Relación con credenciales |
| nombre | CharField(120) | Nombre completo |
| direccion | CharField(200) | Dirección física |
| correo | EmailField (UNIQUE) | Correo de contacto |
| telefono | CharField(20) | Teléfono (10 dígitos) |
| edad | PositiveIntegerField | Edad en años |
| sexo | CharField(1) | "H" (Hombre) o "M" (Mujer) |

#### Cita
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | BigAutoField (PK) | Identificador único |
| paciente | ForeignKey → Paciente | Paciente asociado |
| fecha | DateField | Fecha de la cita |
| hora | TimeField | Hora de la cita |
| estado | CharField(20) | "programada", "cancelada", "atendida" |

**Restricción:** `UniqueConstraint` en (fecha, hora) cuando estado="programada"

#### Consulta (🔒 Campos cifrados)
| Campo | Tipo | Almacenamiento |
|-------|------|----------------|
| id | BigAutoField (PK) | Texto plano |
| cita | OneToOneField → Cita | Texto plano |
| temperatura | EncryptedCharField(512) | **Cifrado AES-256** |
| peso | EncryptedCharField(512) | **Cifrado AES-256** |
| altura | EncryptedCharField(512) | **Cifrado AES-256** |
| presion_arterial | EncryptedCharField(512) | **Cifrado AES-256** |
| fecha_registro | DateTimeField | Texto plano |

#### Historial (🔒 Campos cifrados)
| Campo | Tipo | Almacenamiento |
|-------|------|----------------|
| id | BigAutoField (PK) | Texto plano |
| consulta | OneToOneField → Consulta | Texto plano |
| diagnostico | EncryptedTextField | **Cifrado AES-256** |
| resultados | EncryptedTextField | **Cifrado AES-256** |
| prescripciones | EncryptedTextField | **Cifrado AES-256** |

#### AuditLog
| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | BigAutoField (PK) | Identificador único |
| usuario | ForeignKey → Usuario | Quién realizó la acción |
| accion | CharField(20) | "crear", "editar", "ver", "eliminar" |
| modelo | CharField(50) | Modelo afectado |
| objeto_id | PositiveIntegerField | ID del objeto afectado |
| descripcion | TextField | Detalle de la acción |
| fecha | DateTimeField | Marca de tiempo |
| ip | GenericIPAddressField | IP del cliente |

### 2.3 Manejo de Campos Cifrados

Los campos clínicos sensibles se cifran de forma transparente mediante campos personalizados de Django:

```python
class EncryptedTextField(models.TextField):
    def get_prep_value(self, value):    # Antes de guardar → cifrar
        return encrypt(value)

    def from_db_value(self, value, ...):  # Al leer → descifrar
        return decrypt(value)
```

**Algoritmo primario:** AES-256-GCM (con librería `cryptography`)  
**Algoritmo de respaldo:** HMAC-SHA256 en modo contador (stdlib puro)

La clave de cifrado se almacena en la variable de entorno `CLINICAL_DATA_KEY` (32 bytes, codificada en base64) y **nunca** se incluye en el código fuente.

---

## 3. Especificación de Servicios Web / API

### 3.1 Servidor Principal (Django - puerto 8000)

#### Rutas Públicas (sin autenticación)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET/POST | `/` | Inicio de sesión |
| GET/POST | `/signup/` | Auto-registro de pacientes |
| POST | `/logout/` | Cerrar sesión |

#### Rutas Protegidas (requieren login)

| Método | Ruta | Rol requerido | Descripción |
|--------|------|---------------|-------------|
| GET | `/dashboard/` | Cualquiera | Panel principal con estadísticas |
| GET | `/pacientes/` | Médico | Lista de pacientes |
| GET/POST | `/registrar_paciente/` | Médico | Crear paciente |
| GET/POST | `/pacientes/<id>/editar/` | Médico | Editar paciente |
| POST | `/pacientes/<id>/eliminar/` | Médico | Eliminar paciente |
| GET | `/citas/` | Cualquiera | Lista de citas (filtrada por rol) |
| GET/POST | `/registrar_cita/` | Cualquiera | Crear cita (con exclusión mutua) |
| GET/POST | `/citas/<id>/editar/` | Cualquiera | Editar cita |
| POST | `/citas/<id>/eliminar/` | Cualquiera | Cancelar cita |
| GET | `/historial/` | Cualquiera | Ver historiales clínicos |
| GET/POST | `/registrar_consulta/<cita_id>/` | Médico | Crear historial |
| GET/POST | `/historial/<id>/editar/` | Médico | Editar historial |
| GET | `/reportes/` | Médico | Reportes generales |
| GET/POST | `/cambiar_password/` | Cualquiera | Cambiar contraseña |
| GET | `/auditoria/` | Médico | Registro de auditoría |

#### Autenticación

- **Mecanismo:** Sesiones de Django (`django.contrib.sessions`)
- **Almacenamiento:** Cookies firmadas con `SECRET_KEY`
- **Duración:** 30 minutos (`SESSION_COOKIE_AGE = 1800`)
- **Protección CSRF:** Token CSRF obligatorio en todos los formularios POST
- **Hashing de contraseñas:** PBKDF2-SHA256 con salt aleatorio (Django predeterminado)

#### Manejo de Errores

| Situación | Respuesta |
|-----------|-----------|
| Usuario no autenticado | Redirige a `/` (login) |
| Paciente intenta acceso de médico | HTTP 403 Forbidden |
| Recurso no encontrado | HTTP 404 Not Found |
| Conflicto de horario (cita) | Mensaje de error en la misma vista |
| Error del servidor de tokens | Mensaje de error: "Error de comunicación" |
| Violación de integridad (BD) | Mensaje de error con detalle |

### 3.2 Servidor de Tokens (Flask - puerto 5001)

#### Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/solicitar_token` | Solicitar acceso exclusivo a un horario |
| POST | `/liberar_token` | Liberar el token de un horario |

#### Autenticación Interna

Todas las peticiones requieren el header:
```
X-Internal-Auth: <TOKEN_SERVER_SECRET>
```

Sin este header, el servidor responde `401 Unauthorized`.

#### POST `/solicitar_token`

**Request:**
```json
{
  "fecha": "2026-06-15",
  "hora": "10:00:00"
}
```

**Respuestas:**

| Código | Situación | Body |
|--------|-----------|------|
| 200 | Token concedido | `{"status": "granted", "token": "TOKEN_2026-06-15_10:00:00_1779651838"}` |
| 409 | Slot ya bloqueado | `{"status": "denied", "message": "Token para este horario retenido por otro proceso"}` |
| 400 | Parámetros faltantes | `{"status": "error", "message": "Faltan parámetros"}` |
| 401 | Sin autenticación | `{"status": "error", "message": "No autorizado"}` |

#### POST `/liberar_token`

**Request:**
```json
{
  "fecha": "2026-06-15",
  "hora": "10:00:00"
}
```

**Respuesta:** `200 {"status": "released"}`

#### TTL (Time-To-Live)

Los tokens expiran automáticamente después de **10 segundos**. Esto previene deadlocks si el cliente falla entre la adquisición y liberación del token.

---

## 4. Descripción de la Interfaz de Usuario

### 4.1 Vistas del Sistema

| Vista | Acceso | Descripción |
|-------|--------|-------------|
| VistaLogin | Público | Formulario de inicio de sesión |
| VistaSignup | Público | Auto-registro de pacientes |
| VistaDashboard | Autenticado | Panel con estadísticas resumen |
| VistaPacientes | Médico | Lista CRUD de pacientes |
| VistaRegistroPaciente | Médico | Formulario crear/editar paciente |
| VistaCitas | Autenticado | Calendario/lista de citas |
| VistaRegistroCita | Autenticado | Formulario crear/editar cita |
| VistaHistorial | Autenticado | Registros clínicos con filtro |
| VistaRegistroConsulta | Médico | Formulario crear/editar consulta |
| VistaReportes | Médico | Vista consolidada de reportes |
| VistaCambiarPassword | Autenticado | Cambio de contraseña |
| VistaAuditoria | Médico | Tabla de logs de auditoría |

### 4.2 Flujos de Trabajo

#### Flujo del Paciente

```
Login/Signup ──► Dashboard ──► Mis Citas ──► Agendar Cita
                    │                              │
                    │                    (exclusión mutua)
                    │                              │
                    └──► Mi Historial ◄────── Cita atendida
                    │
                    └──► Cambiar Contraseña
```

#### Flujo del Médico/Administrador

```
Login ──► Dashboard ──► Pacientes ──► CRUD completo
              │
              ├──► Citas ──► Agendar / Editar / Cancelar
              │
              ├──► Historial ──► Registrar consulta ──► Editar historial
              │                     (signos vitales + diagnóstico + receta)
              │
              ├──► Reportes (pacientes, citas, historiales)
              │
              ├──► Auditoría (logs de acceso/modificación)
              │
              └──► Cambiar Contraseña
```

### 4.3 Diseño Visual

- **Framework CSS:** Estilos personalizados (`styles.css`)
- **Layout:** Sidebar fijo + área de contenido principal
- **Responsivo:** Meta viewport para dispositivos móviles
- **Feedback:** Mensajes flash (success/error/warning) con auto-desvanecimiento (3s)
- **Formularios:** Validación del lado del servidor con mensajes por campo

---

## 5. Control de Concurrencia

### 5.1 Problema

En un sistema distribuido donde múltiples usuarios pueden intentar agendar la misma hora simultáneamente, se producen **condiciones de carrera** (race conditions). Sin control, dos pacientes podrían reservar el mismo horario.

### 5.2 Solución: Exclusión Mutua Distribuida Basada en Tokens

El sistema implementa un **servidor de tokens centralizado** (Flask) que actúa como coordinador de exclusión mutua, inspirado en el algoritmo de paso de token.

#### Diagrama de Secuencia

```
Paciente A                    Django                    Flask (Tokens)                Django                    Paciente B
    │                            │                          │                            │                          │
    │── POST /registrar_cita ──►│                          │                            │◄── POST /registrar_cita ──│
    │                            │── POST /solicitar_token─►│                            │                          │
    │                            │                          │◄─ POST /solicitar_token ───│                          │
    │                            │◄── 200 (granted) ────────│                            │                          │
    │                            │                          │── 409 (denied) ───────────►│                          │
    │                            │                          │                            │── Error: "horario        │
    │                            │                          │                            │   siendo procesado" ────►│
    │                            │                          │                            │                          │
    │                            │── transaction.atomic() ──│                            │                          │
    │                            │   INSERT INTO cita...    │                            │                          │
    │                            │                          │                            │                          │
    │                            │── POST /liberar_token ──►│                            │                          │
    │                            │◄── 200 (released) ───────│                            │                          │
    │◄── Cita confirmada ────────│                          │                            │                          │
```

### 5.3 Mecanismos de Protección

| Capa | Mecanismo | Propósito |
|------|-----------|-----------|
| **Aplicación** | Token server (Flask) | Exclusión mutua distribuida |
| **Base de datos** | `transaction.atomic()` | Atomicidad de la operación |
| **Base de datos** | `UniqueConstraint` | Prevención de duplicados a nivel de BD |
| **Token server** | TTL de 10 segundos | Prevención de deadlocks |
| **Token server** | `threading.Lock` | Thread-safety del diccionario de tokens |

### 5.4 Manejo de Fallos

| Escenario | Comportamiento |
|-----------|---------------|
| Django falla tras adquirir token | TTL libera automáticamente tras 10s |
| Servidor de tokens caído | Django muestra error, no permite reservar |
| Dos requests simultáneos al mismo slot | Solo uno obtiene el token (200), el otro recibe 409 |
| IntegrityError en BD (doble insert) | Capturado y reportado al usuario |

### 5.5 Prueba de Concurrencia

El archivo `test_concurrencia.py` verifica el comportamiento con dos hilos simultáneos:

```
Paciente A → 200 (granted)  ← Obtiene el token
Paciente B → 409 (denied)   ← Exclusión mutua funcionando
```

---

## 6. Mecanismos de Seguridad

### 6.1 Resumen de Capas de Seguridad

```
┌────────────────────────────────────────────────────┐
│              Seguridad en Transporte                │
│    (HTTPS recomendado en producción + cookies      │
│     seguras cuando DEBUG=False)                    │
├────────────────────────────────────────────────────┤
│              Autenticación                          │
│    • Login con usuario/contraseña                  │
│    • Sesiones con timeout de 30 min               │
│    • Roles: MEDICO / PACIENTE                      │
│    • Validación fuerte de contraseñas              │
├────────────────────────────────────────────────────┤
│              Autorización                           │
│    • @login_required en todas las vistas           │
│    • @user_passes_test(es_medico) en vistas admin  │
│    • Pacientes solo ven sus propios datos          │
├────────────────────────────────────────────────────┤
│              Cifrado de Datos                       │
│    • AES-256-GCM (con cryptography) o             │
│    • HMAC-SHA256 stream cipher (stdlib)           │
│    • Clave en variable de entorno                  │
│    • Nonce aleatorio por cada cifrado              │
├────────────────────────────────────────────────────┤
│              Integridad                             │
│    • CSRF tokens en todos los formularios          │
│    • HMAC de autenticación en datos cifrados       │
│    • Validación exhaustiva de formularios          │
├────────────────────────────────────────────────────┤
│              Auditoría                              │
│    • Registro de todas las operaciones sensibles   │
│    • IP del cliente + timestamp + usuario          │
│    • Vista de auditoría para médicos               │
└────────────────────────────────────────────────────┘
```

### 6.2 Cifrado de Datos Clínicos

#### Algoritmo Principal: AES-256-GCM

- **Tamaño de clave:** 256 bits (32 bytes)
- **Modo:** GCM (Galois/Counter Mode) — proporciona confidencialidad + autenticación
- **Nonce:** 12 bytes aleatorios por cada operación de cifrado
- **Formato almacenado:** `base64("AESGCM" + nonce[12] + ciphertext)`

#### Algoritmo de Respaldo: HMAC-SHA256 Stream Cipher

Cuando la librería `cryptography` no está disponible:

- **Derivación de claves:** SHA-256 con separación de dominios (`key + "enc"`, `key + "mac"`)
- **Cifrado:** XOR con keystream generado por HMAC-SHA256 en modo contador
- **Autenticación:** HMAC-SHA256 sobre `nonce + ciphertext`
- **Formato almacenado:** `base64(nonce[16] + ciphertext + tag[32])`

#### Gestión de Claves

```bash
# Generar clave (ejecutar una vez)
python -c "import os,base64; print(base64.b64encode(os.urandom(32)).decode())"

# Configurar en el entorno
export CLINICAL_DATA_KEY="<clave_generada>"
```

### 6.3 Hashing de Contraseñas

Django utiliza **PBKDF2-SHA256** con:
- Salt aleatorio de 128 bits
- 870,000 iteraciones (Django 6.0)
- Las contraseñas nunca se almacenan en texto plano

### 6.4 Validaciones de Seguridad en Formularios

| Validación | Detalle |
|-----------|---------|
| Contraseña | Mín. 8 chars, mayúscula, minúscula, número, símbolo |
| Username | Solo letras, números, punto, guion bajo; único |
| Correo | Dominio en lista permitida; único |
| Teléfono | Exactamente 10 dígitos; no inicia en 0; único |
| Presión arterial | Formato NNN/NNN con rangos fisiológicos válidos |
| Temperatura | Rango 30.0 - 45.0 °C |
| Fechas de cita | No permite fechas pasadas ni horas anteriores |

### 6.5 Protección de Sesiones

| Configuración | Valor | Propósito |
|--------------|-------|-----------|
| `SESSION_COOKIE_AGE` | 1800 (30 min) | Timeout por inactividad |
| `SESSION_EXPIRE_AT_BROWSER_CLOSE` | True | Sesión no persiste al cerrar |
| `SESSION_COOKIE_HTTPONLY` | True | No accesible desde JavaScript |
| `SESSION_COOKIE_SECURE` | True (prod) | Solo se envía por HTTPS |
| `CSRF_COOKIE_HTTPONLY` | True | CSRF no accesible desde JS |

### 6.6 Comunicación Interna Segura

La comunicación entre Django y el servidor de tokens está protegida por un **secreto compartido**:

```python
# Django envía:
headers = {"X-Internal-Auth": settings.TOKEN_SERVER_SECRET}

# Flask valida:
@app.before_request
def verify_auth():
    if request.headers.get("X-Internal-Auth") != SHARED_SECRET:
        return jsonify({"error": "unauthorized"}), 401
```

---

## 7. Configuración y Despliegue

### 7.1 Requisitos Previos

- Python 3.10+
- pip (gestor de paquetes)

### 7.2 Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/JosuehCA/SD-PF.git
cd SD-PF

# 2. Crear entorno virtual
python -m venv myenv

# En Windows:
.\myenv\Scripts\activate
# En Mac/Linux:
source myenv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. (Opcional - recomendado) Instalar cryptography para AES-256-GCM
pip install cryptography
```

### 7.3 Variables de Entorno

Copiar `.env.example` y configurar:

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `DJANGO_SECRET_KEY` | Clave secreta de Django | (generada aleatoriamente) |
| `DJANGO_DEBUG` | Modo debug | `True` (dev) / `False` (prod) |
| `DJANGO_ALLOWED_HOSTS` | Hosts permitidos | `localhost,127.0.0.1` |
| `CLINICAL_DATA_KEY` | Clave AES-256 (base64, 32 bytes) | (generada con script) |
| `TOKEN_SERVER_SECRET` | Secreto compartido Flask-Django | (cadena aleatoria) |
| `TOKEN_SERVER_URL` | URL del servidor de tokens | `http://127.0.0.1:5001` |

### 7.4 Ejecución

```bash
# Terminal 1: Servidor de tokens
cd sistema
python servidor_de_tokens.py

# Terminal 2: Aplicación Django
cd sistema
python manage.py migrate
python manage.py createsuperuser  # Crear médico administrador
python manage.py runserver
```

### 7.5 Acceso

- **Aplicación:** http://127.0.0.1:8000/
- **Admin Django:** http://127.0.0.1:8000/admin/
- **Servidor de tokens:** http://127.0.0.1:5001/ (solo API interna)

### 7.6 Prueba de Concurrencia

```bash
# Con el servidor de tokens ejecutándose:
python test_concurrencia.py
```

---

## Apéndices

### A. Estructura del Proyecto

```
SD-PF/
├── .env.example                 # Variables de entorno requeridas
├── requirements.txt             # Dependencias Python
├── README.md                    # Esta documentación
└── sistema/
    ├── manage.py                # CLI de Django
    ├── servidor_de_tokens.py    # Servidor Flask de exclusión mutua
    ├── test_concurrencia.py     # Prueba de concurrencia
    ├── sistema/                 # Configuración Django
    │   ├── settings.py
    │   ├── urls.py
    │   ├── wsgi.py
    │   └── asgi.py
    └── consultorio/             # Aplicación principal
        ├── models.py            # Modelos (con campos cifrados)
        ├── views.py             # Lógica de vistas
        ├── forms.py             # Formularios con validación
        ├── urls.py              # Rutas de la app
        ├── encryption.py        # Módulo de cifrado AES-256
        ├── fields.py            # Campos Django cifrados
        ├── admin.py             # Configuración admin
        ├── migrations/          # Migraciones de BD
        ├── static/
        │   └── consultorio/
        │       └── styles.css   # Estilos CSS
        └── templates/
            ├── Base.html
            ├── VistaLogin.html
            ├── VistaSignup.html
            ├── VistaDashboard.html
            ├── VistaPacientes.html
            ├── VistaRegistroPaciente.html
            ├── VistaCitas.html
            ├── VistaRegistroCita.html
            ├── VistaHistorial.html
            ├── VistaRegistroConsulta.html
            ├── VistaReportes.html
            ├── VistaCambiarPassword.html
            └── VistaAuditoria.html
```

### B. Tecnologías Utilizadas

| Categoría | Tecnología | Versión |
|-----------|-----------|---------|
| Backend | Django | 6.0.5 |
| Microservicio | Flask | 3.1.3 |
| Base de Datos | SQLite3 | (incluido en Python) |
| Cifrado | AES-256-GCM / HMAC-SHA256 | — |
| HTTP Client | requests | 2.34.2 |
| Frontend | HTML5 + CSS3 + JavaScript | — |
| Lenguaje | Python | 3.10+ |

