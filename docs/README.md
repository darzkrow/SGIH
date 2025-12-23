# Documentación - Plataforma de Gestión de Inventario

## Introducción

Bienvenido a la documentación de la Plataforma de Gestión de Inventario para las 16 Hidrológicas autónomas de Colombia. Esta plataforma proporciona una solución completa para la gestión, transferencia y trazabilidad de inventarios entre organizaciones.

## 📚 Guías Disponibles

### [🚀 Guía de Uso de la API](api-usage-examples.md)
Ejemplos prácticos y completos de cómo usar la API REST, incluyendo:
- Autenticación con JWT
- Gestión de inventario (CRUD completo)
- Workflow de transferencias externas
- Validación de códigos QR
- Sistema de notificaciones
- Casos de uso completos

### [🔄 Guía de Workflows](workflow-guide.md)
Descripción detallada de los procesos de negocio:
- Workflow de transferencias externas
- Movimientos internos
- Gestión de estados de ítems
- Sistema de notificaciones
- Trazabilidad (Ficha de Vida)
- Validación QR
- Mejores prácticas

### [🔌 Guía de Integración](integration-guide.md)
Información completa para integrar sistemas externos:
- SDKs disponibles (Python, JavaScript, C#)
- Webhooks y eventos en tiempo real
- WebSockets para notificaciones
- Integración con sistemas ERP
- Monitoreo y métricas
- Mejores prácticas de integración

## 🏗️ Arquitectura del Sistema

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Gateway   │    │   Backend       │
│   (React)       │◄──►│   (Nginx)       │◄──►│   (Django)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                       ┌─────────────────┐             │
                       │   Database      │◄────────────┘
                       │   (PostgreSQL)  │
                       └─────────────────┘
                                │
                       ┌─────────────────┐
                       │   Cache/Queue   │
                       │   (Redis)       │
                       └─────────────────┘
```

## 🌟 Características Principales

### Multitenencia
- **Aislamiento de datos**: Cada hidrológica solo ve sus propios datos
- **Vista global**: El Ente Rector tiene acceso a datos anonimizados de todas las hidrológicas
- **Filtrado automático**: Los datos se filtran automáticamente según el contexto del usuario

### Control de Acceso (RBAC)
- **Ente Rector**: Supervisión y vista global del sistema
- **Operador Hidrológica**: Gestión completa del inventario local
- **Punto Control**: Validación de QR y confirmaciones de transferencias

### Transferencias Externas
- **Workflow completo**: Solicitud → Aprobación → Orden → Transporte → Completación
- **Códigos QR**: Validación segura con firmas digitales
- **PDFs automáticos**: Generación de órdenes de traspaso con QR
- **Notificaciones**: Alertas automáticas en cada etapa

### Trazabilidad Completa
- **Ficha de Vida**: Historial completo de cada ítem
- **Eventos registrados**: Creación, movimientos, cambios de estado, transferencias
- **Auditoría**: Trazabilidad completa para cumplimiento normativo

## 🔧 Tecnologías Utilizadas

### Backend
- **Django 4.2**: Framework web principal
- **Django REST Framework**: API REST
- **PostgreSQL**: Base de datos principal
- **Redis**: Cache y cola de tareas
- **Celery**: Procesamiento asíncrono

### Frontend
- **React**: Interfaz de usuario
- **Material-UI**: Componentes de interfaz
- **Redux**: Gestión de estado
- **Axios**: Cliente HTTP

### Infraestructura
- **Docker**: Contenedorización
- **Nginx**: Proxy reverso y servidor web
- **Gunicorn**: Servidor WSGI
- **Docker Compose**: Orquestación de contenedores

## 📖 Documentación Interactiva

### Swagger UI
Interfaz interactiva para explorar y probar la API:
```
http://localhost:8000/api/docs/
```

### ReDoc
Documentación alternativa con mejor formato:
```
http://localhost:8000/api/redoc/
```

### Schema OpenAPI
Esquema JSON de la API:
```
http://localhost:8000/api/schema/
```

## 🚀 Inicio Rápido

### 1. Configuración del Entorno
```bash
# Clonar repositorio
git clone https://github.com/gobierno/inventario-platform.git
cd inventario-platform

# Configurar variables de entorno
cp .env.example .env
# Editar .env con sus configuraciones

# Iniciar servicios
docker-compose up -d
```

### 2. Inicialización de Datos
```bash
# Ejecutar migraciones
docker-compose exec web python manage.py migrate

# Cargar datos iniciales
docker-compose exec web python manage.py bootstrap_system

# Crear superusuario
docker-compose exec web python manage.py createsuperuser
```

### 3. Verificar Instalación
```bash
# Verificar servicios
curl http://localhost:8000/api/v1/auth/health/

# Acceder a documentación
open http://localhost:8000/api/docs/
```

## 🔐 Autenticación

### Obtener Token
```bash
curl -X POST http://localhost:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "operador@hidrologica.gov.co",
    "password": "password123"
  }'
```

### Usar Token
```bash
curl -X GET http://localhost:8000/api/v1/inventory/items/ \
  -H "Authorization: Bearer <token>"
```

## 📊 Endpoints Principales

### Autenticación
- `POST /api/v1/auth/token/` - Obtener token de acceso
- `POST /api/v1/auth/token/refresh/` - Refrescar token
- `POST /api/v1/auth/logout/` - Cerrar sesión

### Inventario
- `GET /api/v1/inventory/items/` - Listar ítems
- `POST /api/v1/inventory/items/` - Crear ítem
- `GET /api/v1/inventory/items/{id}/` - Obtener ítem
- `PUT /api/v1/inventory/items/{id}/` - Actualizar ítem
- `POST /api/v1/inventory/items/{id}/mover_interno/` - Movimiento interno

### Transferencias
- `GET /api/v1/transfers/external/` - Listar transferencias
- `POST /api/v1/transfers/external/` - Crear transferencia
- `POST /api/v1/transfers/external/{id}/aprobar/` - Aprobar transferencia
- `POST /api/v1/transfers/external/{id}/generar_pdf/` - Generar PDF

### QR Validation
- `GET /api/v1/transfers/qr/validate/` - Validar QR (público)
- `POST /api/v1/transfers/qr/confirm/` - Confirmar con QR (público)

### Notificaciones
- `GET /api/v1/notifications/` - Listar notificaciones
- `POST /api/v1/notifications/{id}/marcar_leida/` - Marcar como leída

## 🔍 Filtrado y Búsqueda

### Parámetros Comunes
- `search` - Búsqueda de texto libre
- `ordering` - Ordenamiento (`-created_at`, `nombre`, etc.)
- `page` - Número de página
- `page_size` - Tamaño de página (máximo 100)

### Filtros Específicos
- **Inventario**: `tipo`, `estado`, `categoria`, `acueducto_actual`
- **Transferencias**: `estado`, `prioridad`, `hidrologica_origen`
- **Notificaciones**: `leida`, `tipo`, `fecha_desde`

## 📈 Monitoreo y Métricas

### Métricas Disponibles
```
GET /metrics
```

### Dashboards
- **Grafana**: Métricas de sistema y negocio
- **Prometheus**: Recolección de métricas
- **Logs**: Structured logging con ELK Stack

## 🛠️ Desarrollo

### Estructura del Proyecto
```
inventory_platform/
├── apps/
│   ├── core/           # Modelos base y autenticación
│   ├── inventory/      # Gestión de inventario
│   ├── transfers/      # Transferencias y QR
│   └── notifications/  # Sistema de notificaciones
├── docs/              # Documentación
├── fixtures/          # Datos de prueba
└── inventory_platform/ # Configuración Django
```

### Comandos de Desarrollo
```bash
# Ejecutar tests
docker-compose exec web python manage.py test

# Crear migraciones
docker-compose exec web python manage.py makemigrations

# Shell interactivo
docker-compose exec web python manage.py shell

# Cargar fixtures
docker-compose exec web python manage.py loaddata fixtures/test_data.json
```

## 🐛 Resolución de Problemas

### Problemas Comunes

#### Error 401 - No autorizado
```bash
# Verificar token
curl -X GET http://localhost:8000/api/v1/auth/verify/ \
  -H "Authorization: Bearer <token>"
```

#### Error 429 - Rate limit
```bash
# Esperar y reintentar
sleep 60
```

#### Servicios no disponibles
```bash
# Verificar estado de contenedores
docker-compose ps

# Ver logs
docker-compose logs web
```

### Logs de Diagnóstico
```bash
# Logs de aplicación
docker-compose logs -f web

# Logs de base de datos
docker-compose logs -f db

# Logs de Redis
docker-compose logs -f redis
```

## 📞 Soporte

### Contacto
- **Email**: soporte@inventario.gov.co
- **Documentación**: https://docs.inventario.gov.co
- **Issues**: https://github.com/gobierno/inventario-platform/issues

### Horarios de Soporte
- **Lunes a Viernes**: 8:00 AM - 6:00 PM (COT)
- **Emergencias**: 24/7 (solo para issues críticos)

### Escalación
1. **Nivel 1**: Documentación y FAQ
2. **Nivel 2**: Soporte técnico por email
3. **Nivel 3**: Soporte especializado por teléfono

## 📝 Changelog

### v1.0.0 (2024-01-20)
- ✅ Implementación completa del sistema base
- ✅ Multitenencia y RBAC
- ✅ Workflow de transferencias externas
- ✅ Sistema de QR con firmas digitales
- ✅ Notificaciones en tiempo real
- ✅ Trazabilidad completa (Ficha de Vida)
- ✅ API REST completa con documentación
- ✅ Integración con sistemas externos

## 📄 Licencia

Este proyecto está licenciado bajo los términos del Gobierno de Colombia. Para más información, consulte el archivo LICENSE en el repositorio.

---

**¿Necesita ayuda?** Consulte las guías específicas o contacte al equipo de soporte técnico.