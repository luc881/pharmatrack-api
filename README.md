# 🏥 POS System API

API REST para gestión de inventario y ventas de una farmacia, desarrollada con **FastAPI**, **SQLAlchemy** y **PostgreSQL**. Incluye autenticación JWT, control de permisos por roles, gestión de productos con lotes, ventas, compras y más.

---

## 🛠️ Stack tecnológico

- **Python 3.13**
- **FastAPI** — framework web
- **SQLAlchemy** — ORM
- **Alembic** — migraciones de base de datos
- **PostgreSQL** — base de datos
- **Pydantic v2** — validación de datos
- **pydantic-settings** — gestión de variables de entorno
- **Poetry** — gestión de dependencias
- **JWT (python-jose)** — autenticación
- **Passlib + Bcrypt** — hashing de contraseñas
- **Uvicorn** — servidor ASGI
- **SlowAPI** — rate limiting

---

## 📁 Estructura del proyecto

```
POSSystem/
├── migrations/              # Migraciones de Alembic
│   ├── versions/
│   └── env.py
├── logs/                    # Logs locales (solo desarrollo, gitignored)
├── src/possystem/
│   ├── api/routes/          # Endpoints por módulo
│   ├── db/
│   │   └── session.py       # Configuración de SQLAlchemy
│   ├── models/              # ORM + Schemas Pydantic por módulo
│   │   ├── products/
│   │   ├── sales/
│   │   ├── users/
│   │   └── ...
│   ├── scripts/             # Scripts de desarrollo
│   │   ├── reset_db.py
│   │   └── reset_migrations.py
│   ├── seeds/               # Datos iniciales
│   ├── types/               # Tipos personalizados de Pydantic
│   ├── utils/               # Helpers
│   │   ├── pagination.py    # Paginación genérica
│   │   ├── permissions.py   # Dependencias de permisos
│   │   ├── rate_limit.py    # Configuración de rate limiting
│   │   ├── logger.py        # Helper de logging
│   │   ├── security.py      # JWT y autenticación
│   │   └── validators.py    # Validaciones de negocio
│   ├── config.py            # Settings con pydantic-settings
│   ├── logging_config.py    # Configuración del sistema de logs
│   └── main.py
├── .env.example
├── alembic.ini
├── Procfile
└── pyproject.toml
```

---

## ⚙️ Instalación y configuración

### 1. Requisitos previos

- Python 3.13+
- PostgreSQL corriendo localmente
- Poetry instalado (`pip install poetry`)

### 2. Clonar el repositorio

```bash
git clone <url-del-repo>
cd POSSystem
```

### 3. Instalar dependencias

```bash
poetry install
```

### 4. Configurar variables de entorno

```bash
cp .env.example .env
```

Edita el `.env` con tus valores:

```env
# Base de datos
DATABASE_URL=postgresql://usuario:password@localhost/nombre_bd

# JWT
SECRET_KEY=tu_clave_secreta_aqui
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# App
ENVIRONMENT=development
LOG_LEVEL=DEBUG

# CORS (solo necesario en producción)
# ALLOWED_ORIGINS=["https://tu-frontend.com"]
```

Para generar una `SECRET_KEY` segura:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 5. Aplicar migraciones

```bash
alembic upgrade head
```

### 6. Arrancar el servidor

```bash
uvicorn possystem.main:app --reload
```

La API estará disponible en `http://localhost:8000`.
Documentación interactiva en `http://localhost:8000/docs`.

---

## 🧪 Scripts de desarrollo

```bash
# Resetear datos y re-correr seeds (mantiene las migraciones)
poetry run reset-db

# Regenerar migración inicial desde cero (cuando cambiaste un ORM)
poetry run reset-migrations
```

> ⚠️ Estos scripts solo funcionan con `ENVIRONMENT=development`. Están bloqueados en producción.

---

## 🔐 Autenticación

La API usa **JWT Bearer tokens**. Para obtener un token:

```http
POST /auth/token
Content-Type: application/x-www-form-urlencoded

username=correo@ejemplo.com&password=tu_password
```

Incluye el token en las siguientes peticiones:

```http
Authorization: Bearer <token>
```

---

## 🚦 Rate Limiting

Los endpoints están protegidos contra abuso con los siguientes límites por IP:

| Tipo | Límite | Aplica en |
|---|---|---|
| Autenticación | 5 / minuto | `POST /auth/token` |
| Lectura | 60 / minuto | `GET /` en todos los módulos |
| Búsqueda | 40 / minuto | `GET /search` en todos los módulos |
| Escritura | 30 / minuto | `POST`, `PUT`, `DELETE` |

Cuando se supera el límite la API responde con `429 Too Many Requests`.

---

## 📄 Paginación

Todos los endpoints de listado soportan paginación:

```http
GET /products?page=1&page_size=20
```

Respuesta:

```json
{
  "data": [...],
  "total": 87,
  "page": 1,
  "page_size": 20,
  "total_pages": 5,
  "has_next": true,
  "has_prev": false
}
```

---

## 📦 Módulos principales

| Módulo | Prefijo | Descripción |
|---|---|---|
| Auth | `/auth` | Login y generación de tokens |
| Users | `/users` | Gestión de usuarios |
| Roles | `/roles` | Roles y asignación de permisos |
| Permissions | `/permissions` | Catálogo de permisos |
| Products | `/products` | Catálogo de productos |
| Product Batches | `/productsbatches` | Lotes con fecha de caducidad y stock |
| Product Categories | `/productscategories` | Árbol jerárquico de categorías |
| Product Brand | `/productsbrand` | Marcas de productos |
| Product Master | `/productsmaster` | Productos genéricos (maestros) |
| Ingredients | `/ingredients` | Ingredientes activos |
| Sales | `/sales` | Ventas (draft → completed) |
| Sale Details | `/saledetails` | Líneas de detalle de venta |
| Sale Payments | `/salepayments` | Pagos asociados a ventas |
| Refund Products | `/refundproducts` | Devoluciones |
| Suppliers | `/suppliers` | Proveedores |
| Purchases | `/purchases` | Órdenes de compra |
| Branches | `/branches` | Sucursales |

---

## 📋 Logging

El sistema de logs se configura automáticamente según el entorno:

| Entorno | Nivel | Destino |
|---|---|---|
| `development` | `DEBUG` | Consola + `logs/app.log` |
| `production` | `INFO` | Consola (Railway logs) |

Los archivos de log rotan automáticamente cada 5MB conservando los últimos 3 archivos.

---

## 🗄️ Migraciones con Alembic

```bash
# Aplicar todas las migraciones pendientes
alembic upgrade head

# Crear nueva migración tras cambiar un ORM
alembic revision --autogenerate -m "descripcion del cambio"

# Ver historial de migraciones
alembic history

# Revertir la última migración
alembic downgrade -1
```

---

## 🚀 Deploy en Railway

1. Crea un nuevo proyecto en [Railway](https://railway.app)
2. Conecta tu repositorio
3. Agrega las variables de entorno del `.env.example` en el panel de Railway
4. El `Procfile` incluido arranca la app automáticamente:

```
web: alembic upgrade head && uvicorn possystem.main:app --host 0.0.0.0 --port $PORT
```

### Variables requeridas en Railway

```env
DATABASE_URL=postgresql://...
SECRET_KEY=...
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ENVIRONMENT=production
LOG_LEVEL=INFO
ALLOWED_ORIGINS=["https://tu-frontend.com"]
```

---

## 📝 Licencia

Proyecto académico — Opción a titulación.