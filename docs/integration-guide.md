# Guía de Integración - Plataforma de Gestión de Inventario

## Introducción

Esta guía proporciona información detallada para integrar sistemas externos con la Plataforma de Gestión de Inventario, incluyendo autenticación, webhooks, SDKs y mejores prácticas de integración.

## 1. Arquitectura de Integración

### 1.1 Componentes del Sistema

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

### 1.2 Puntos de Integración

#### API REST
- **URL Base**: `https://api.inventario.gov.co/api/v1/`
- **Protocolo**: HTTPS
- **Formato**: JSON
- **Autenticación**: JWT Bearer Token

#### Webhooks
- **Eventos**: Transferencias, cambios de estado, notificaciones
- **Formato**: JSON POST
- **Seguridad**: HMAC-SHA256 signature

#### WebSockets (Tiempo Real)
- **URL**: `wss://api.inventario.gov.co/ws/`
- **Protocolo**: WebSocket
- **Autenticación**: JWT Token

## 2. Autenticación y Autorización

### 2.1 Obtener Credenciales de API

#### Para Sistemas Externos
1. Contactar al administrador del sistema
2. Proporcionar información del sistema integrador
3. Recibir `client_id` y `client_secret`
4. Configurar endpoints de callback (para webhooks)

#### Para Aplicaciones de Usuario
1. Usar credenciales de usuario existentes
2. Implementar flujo OAuth2 (opcional)
3. Manejar refresh tokens apropiadamente

### 2.2 Flujo de Autenticación

#### Autenticación de Sistema (Client Credentials)
```bash
curl -X POST https://api.inventario.gov.co/api/v1/auth/token/system/ \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "your_client_id",
    "client_secret": "your_client_secret",
    "grant_type": "client_credentials"
  }'
```

**Respuesta:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "read write"
}
```

#### Autenticación de Usuario
```bash
curl -X POST https://api.inventario.gov.co/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "usuario@hidrologica.gov.co",
    "password": "password123"
  }'
```

### 2.3 Uso del Token

```bash
curl -X GET https://api.inventario.gov.co/api/v1/inventory/items/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

## 3. SDKs y Librerías

### 3.1 SDK Python

#### Instalación
```bash
pip install inventario-platform-sdk
```

#### Uso Básico
```python
from inventario_sdk import InventarioClient

# Inicializar cliente
client = InventarioClient(
    base_url="https://api.inventario.gov.co/api/v1/",
    client_id="your_client_id",
    client_secret="your_client_secret"
)

# Listar ítems
items = client.inventory.list_items(
    filters={'tipo': 'tuberia', 'estado': 'disponible'}
)

# Crear transferencia
transfer = client.transfers.create_external_transfer(
    hidrologica_destino_id="uuid-here",
    items=[
        {'item_id': 'uuid-here', 'cantidad_solicitada': 10}
    ],
    motivo="Emergencia"
)

# Aprobar transferencia
client.transfers.approve_transfer(
    transfer_id=transfer.id,
    items_aprobados=[
        {'item_transferencia_id': 'uuid-here', 'cantidad_aprobada': 8}
    ]
)
```

### 3.2 SDK JavaScript/Node.js

#### Instalación
```bash
npm install inventario-platform-sdk
```

#### Uso Básico
```javascript
const { InventarioClient } = require('inventario-platform-sdk');

// Inicializar cliente
const client = new InventarioClient({
  baseUrl: 'https://api.inventario.gov.co/api/v1/',
  clientId: 'your_client_id',
  clientSecret: 'your_client_secret'
});

// Listar ítems
const items = await client.inventory.listItems({
  tipo: 'tuberia',
  estado: 'disponible'
});

// Crear transferencia
const transfer = await client.transfers.createExternalTransfer({
  hidrologica_destino_id: 'uuid-here',
  items: [
    { item_id: 'uuid-here', cantidad_solicitada: 10 }
  ],
  motivo: 'Emergencia'
});
```

### 3.3 SDK C# (.NET)

#### Instalación
```bash
dotnet add package InventarioPlatform.SDK
```

#### Uso Básico
```csharp
using InventarioPlatform.SDK;

// Inicializar cliente
var client = new InventarioClient(new InventarioClientOptions
{
    BaseUrl = "https://api.inventario.gov.co/api/v1/",
    ClientId = "your_client_id",
    ClientSecret = "your_client_secret"
});

// Listar ítems
var items = await client.Inventory.ListItemsAsync(new ItemFilter
{
    Tipo = "tuberia",
    Estado = "disponible"
});

// Crear transferencia
var transfer = await client.Transfers.CreateExternalTransferAsync(new CreateTransferRequest
{
    HidrologicaDestinoId = Guid.Parse("uuid-here"),
    Items = new[]
    {
        new TransferItem { ItemId = Guid.Parse("uuid-here"), CantidadSolicitada = 10 }
    },
    Motivo = "Emergencia"
});
```

## 4. Webhooks

### 4.1 Configuración de Webhooks

#### Registrar Webhook
```bash
curl -X POST https://api.inventario.gov.co/api/v1/webhooks/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-system.com/webhooks/inventario",
    "events": ["transfer.approved", "transfer.completed", "item.state_changed"],
    "secret": "your_webhook_secret"
  }'
```

#### Eventos Disponibles
- `transfer.created`: Nueva transferencia solicitada
- `transfer.approved`: Transferencia aprobada
- `transfer.rejected`: Transferencia rechazada
- `transfer.completed`: Transferencia completada
- `item.created`: Nuevo ítem creado
- `item.state_changed`: Estado de ítem cambiado
- `item.moved`: Ítem movido internamente
- `notification.sent`: Notificación enviada

### 4.2 Estructura de Webhook

#### Headers
```
POST /webhooks/inventario HTTP/1.1
Host: your-system.com
Content-Type: application/json
X-Inventario-Event: transfer.approved
X-Inventario-Signature: sha256=<signature>
X-Inventario-Delivery: 12345678-1234-1234-1234-123456789012
```

#### Payload
```json
{
  "event": "transfer.approved",
  "timestamp": "2024-01-20T14:30:00Z",
  "data": {
    "transfer": {
      "id": "550e8400-e29b-41d4-a716-446655440060",
      "numero_solicitud": "SOL-2024-001",
      "estado": "aprobada",
      "hidrologica_origen": {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "nombre": "Hidrológica del Atlántico",
        "codigo": "HAT"
      },
      "hidrologica_destino": {
        "id": "550e8400-e29b-41d4-a716-446655440002",
        "nombre": "Hidrológica de Bolívar",
        "codigo": "HBL"
      },
      "items": [
        {
          "item": {
            "id": "550e8400-e29b-41d4-a716-446655440020",
            "sku": "TUB-PVC-001",
            "nombre": "Tubería PVC 4 pulgadas"
          },
          "cantidad_solicitada": 10,
          "cantidad_aprobada": 8
        }
      ],
      "aprobado_por": {
        "id": "550e8400-e29b-41d4-a716-446655440011",
        "username": "operador.hbl@example.com",
        "hidrologica": "HBL"
      },
      "fecha_aprobacion": "2024-01-20T14:30:00Z"
    }
  }
}
```

### 4.3 Validación de Webhooks

#### Verificar Firma
```python
import hmac
import hashlib

def verify_webhook_signature(payload, signature, secret):
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(
        f"sha256={expected_signature}",
        signature
    )

# Uso
payload = request.body
signature = request.headers.get('X-Inventario-Signature')
secret = 'your_webhook_secret'

if verify_webhook_signature(payload, signature, secret):
    # Procesar webhook
    process_webhook(json.loads(payload))
else:
    # Rechazar webhook
    return 401
```

## 5. WebSockets (Tiempo Real)

### 5.1 Conexión WebSocket

#### JavaScript
```javascript
const ws = new WebSocket('wss://api.inventario.gov.co/ws/notifications/');

ws.onopen = function(event) {
    // Autenticar
    ws.send(JSON.stringify({
        type: 'auth',
        token: 'your_jwt_token'
    }));
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    
    switch(data.type) {
        case 'notification':
            handleNotification(data.payload);
            break;
        case 'transfer_update':
            handleTransferUpdate(data.payload);
            break;
        case 'inventory_update':
            handleInventoryUpdate(data.payload);
            break;
    }
};
```

#### Python
```python
import asyncio
import websockets
import json

async def connect_websocket():
    uri = "wss://api.inventario.gov.co/ws/notifications/"
    
    async with websockets.connect(uri) as websocket:
        # Autenticar
        await websocket.send(json.dumps({
            'type': 'auth',
            'token': 'your_jwt_token'
        }))
        
        # Escuchar mensajes
        async for message in websocket:
            data = json.loads(message)
            await handle_message(data)

async def handle_message(data):
    if data['type'] == 'notification':
        print(f"Nueva notificación: {data['payload']['mensaje']}")
    elif data['type'] == 'transfer_update':
        print(f"Actualización de transferencia: {data['payload']['estado']}")
```

### 5.2 Suscripciones

#### Suscribirse a Eventos
```javascript
// Suscribirse a notificaciones de una hidrológica específica
ws.send(JSON.stringify({
    type: 'subscribe',
    channel: 'hidrologica.550e8400-e29b-41d4-a716-446655440001'
}));

// Suscribirse a actualizaciones de transferencias
ws.send(JSON.stringify({
    type: 'subscribe',
    channel: 'transfers'
}));

// Suscribirse a cambios de inventario
ws.send(JSON.stringify({
    type: 'subscribe',
    channel: 'inventory'
}));
```

## 6. Integración con Sistemas ERP

### 6.1 SAP Integration

#### Configuración
```xml
<!-- SAP PI/PO Configuration -->
<integration>
    <sender>
        <system>SAP_ERP</system>
        <client>100</client>
    </sender>
    <receiver>
        <system>INVENTARIO_PLATFORM</system>
        <endpoint>https://api.inventario.gov.co/api/v1/</endpoint>
    </receiver>
    <mapping>
        <source>IDOC_MATMAS05</source>
        <target>ItemInventario</target>
    </mapping>
</integration>
```

#### Mapeo de Datos
```python
# Mapeo SAP -> Plataforma Inventario
def map_sap_to_inventario(sap_material):
    return {
        'sku': sap_material['MATNR'],
        'nombre': sap_material['MAKTX'],
        'descripcion': sap_material['MAKTG'],
        'tipo': map_material_type(sap_material['MTART']),
        'categoria_id': get_category_id(sap_material['MATKL']),
        'valor_unitario': sap_material['STPRS'],
        'unidad_medida': sap_material['MEINS']
    }
```

### 6.2 Oracle ERP Integration

#### Configuración
```sql
-- Oracle Integration usando REST Services
BEGIN
    ORDS.ENABLE_SCHEMA(
        p_enabled => TRUE,
        p_schema => 'INVENTARIO_INT',
        p_url_mapping_type => 'BASE_PATH',
        p_url_mapping_pattern => 'inventario',
        p_auto_rest_auth => TRUE
    );
END;
```

#### Procedimiento de Sincronización
```sql
CREATE OR REPLACE PROCEDURE sync_inventory_item(
    p_item_id IN VARCHAR2,
    p_action IN VARCHAR2
) AS
    l_response CLOB;
    l_http_request UTL_HTTP.req;
    l_http_response UTL_HTTP.resp;
BEGIN
    -- Preparar request HTTP
    l_http_request := UTL_HTTP.begin_request(
        url => 'https://api.inventario.gov.co/api/v1/inventory/items/',
        method => 'POST'
    );
    
    -- Agregar headers
    UTL_HTTP.set_header(l_http_request, 'Authorization', 'Bearer ' || get_api_token());
    UTL_HTTP.set_header(l_http_request, 'Content-Type', 'application/json');
    
    -- Enviar datos
    UTL_HTTP.write_text(l_http_request, build_item_json(p_item_id));
    
    -- Procesar respuesta
    l_http_response := UTL_HTTP.get_response(l_http_request);
    UTL_HTTP.read_text(l_http_response, l_response);
    
    -- Log resultado
    log_integration_result(p_item_id, l_response);
    
    UTL_HTTP.end_response(l_http_response);
END;
```

## 7. Integración con Sistemas de Monitoreo

### 7.1 Prometheus Metrics

#### Endpoint de Métricas
```
GET /metrics
```

#### Métricas Disponibles
```
# HELP inventario_transfers_total Total number of transfers
# TYPE inventario_transfers_total counter
inventario_transfers_total{status="completed",hidrologica="HAT"} 150

# HELP inventario_items_total Total number of inventory items
# TYPE inventario_items_total gauge
inventario_items_total{type="tuberia",status="disponible"} 1250

# HELP inventario_api_requests_total Total API requests
# TYPE inventario_api_requests_total counter
inventario_api_requests_total{method="GET",endpoint="/inventory/items",status="200"} 5432
```

### 7.2 Grafana Dashboard

#### Configuración de Data Source
```json
{
  "name": "Inventario Platform",
  "type": "prometheus",
  "url": "https://api.inventario.gov.co/metrics",
  "access": "proxy",
  "basicAuth": true,
  "basicAuthUser": "monitoring",
  "basicAuthPassword": "password"
}
```

#### Queries de Ejemplo
```promql
# Transferencias por hora
rate(inventario_transfers_total[1h])

# Ítems disponibles por tipo
sum(inventario_items_total{status="disponible"}) by (type)

# Tiempo de respuesta API
histogram_quantile(0.95, rate(inventario_api_duration_seconds_bucket[5m]))
```

## 8. Integración con Sistemas de Notificación

### 8.1 Slack Integration

#### Configuración
```python
from slack_sdk import WebClient

class SlackNotificationService:
    def __init__(self, token):
        self.client = WebClient(token=token)
    
    def send_transfer_notification(self, transfer):
        message = f"""
        🚚 Nueva transferencia aprobada
        
        *Solicitud:* {transfer.numero_solicitud}
        *Origen:* {transfer.hidrologica_origen.nombre}
        *Destino:* {transfer.hidrologica_destino.nombre}
        *Ítems:* {len(transfer.items.all())}
        
        <{transfer.get_absolute_url()}|Ver detalles>
        """
        
        self.client.chat_postMessage(
            channel='#inventario-alerts',
            text=message,
            username='Inventario Bot'
        )
```

### 8.2 Microsoft Teams Integration

#### Webhook Configuration
```python
import requests

def send_teams_notification(webhook_url, transfer):
    payload = {
        "@type": "MessageCard",
        "@context": "https://schema.org/extensions",
        "summary": "Nueva transferencia aprobada",
        "themeColor": "0078D4",
        "sections": [{
            "activityTitle": "Transferencia Aprobada",
            "activitySubtitle": f"Solicitud {transfer.numero_solicitud}",
            "facts": [
                {"name": "Origen", "value": transfer.hidrologica_origen.nombre},
                {"name": "Destino", "value": transfer.hidrologica_destino.nombre},
                {"name": "Ítems", "value": str(len(transfer.items.all()))},
                {"name": "Estado", "value": transfer.get_estado_display()}
            ]
        }],
        "potentialAction": [{
            "@type": "OpenUri",
            "name": "Ver Detalles",
            "targets": [{"os": "default", "uri": transfer.get_absolute_url()}]
        }]
    }
    
    requests.post(webhook_url, json=payload)
```

## 9. Mejores Prácticas de Integración

### 9.1 Manejo de Errores

#### Retry Logic
```python
import time
import random
from functools import wraps

def retry_with_backoff(max_retries=3, base_delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    time.sleep(delay)
            
        return wrapper
    return decorator

@retry_with_backoff(max_retries=3)
def call_api(endpoint, data):
    response = requests.post(endpoint, json=data)
    response.raise_for_status()
    return response.json()
```

#### Circuit Breaker
```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func, *args, **kwargs):
        if self.state == 'OPEN':
            if time.time() - self.last_failure_time > self.timeout:
                self.state = 'HALF_OPEN'
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise e
    
    def on_success(self):
        self.failure_count = 0
        self.state = 'CLOSED'
    
    def on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'
```

### 9.2 Rate Limiting

#### Client-Side Rate Limiting
```python
import time
from collections import deque

class RateLimiter:
    def __init__(self, max_requests=100, time_window=60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
    
    def allow_request(self):
        now = time.time()
        
        # Remover requests antiguos
        while self.requests and self.requests[0] <= now - self.time_window:
            self.requests.popleft()
        
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        
        return False
    
    def wait_time(self):
        if not self.requests:
            return 0
        
        oldest_request = self.requests[0]
        return max(0, self.time_window - (time.time() - oldest_request))
```

### 9.3 Caching

#### Response Caching
```python
import redis
import json
import hashlib

class APICache:
    def __init__(self, redis_client, default_ttl=300):
        self.redis = redis_client
        self.default_ttl = default_ttl
    
    def get_cache_key(self, endpoint, params):
        key_data = f"{endpoint}:{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, endpoint, params):
        cache_key = self.get_cache_key(endpoint, params)
        cached_data = self.redis.get(cache_key)
        
        if cached_data:
            return json.loads(cached_data)
        
        return None
    
    def set(self, endpoint, params, data, ttl=None):
        cache_key = self.get_cache_key(endpoint, params)
        ttl = ttl or self.default_ttl
        
        self.redis.setex(
            cache_key,
            ttl,
            json.dumps(data, default=str)
        )
```

### 9.4 Logging y Monitoreo

#### Structured Logging
```python
import logging
import json
from datetime import datetime

class StructuredLogger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        handler = logging.StreamHandler()
        handler.setFormatter(self.JsonFormatter())
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    class JsonFormatter(logging.Formatter):
        def format(self, record):
            log_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'level': record.levelname,
                'message': record.getMessage(),
                'module': record.module,
                'function': record.funcName,
                'line': record.lineno
            }
            
            if hasattr(record, 'extra_data'):
                log_entry.update(record.extra_data)
            
            return json.dumps(log_entry)
    
    def info(self, message, **kwargs):
        self.logger.info(message, extra={'extra_data': kwargs})
    
    def error(self, message, **kwargs):
        self.logger.error(message, extra={'extra_data': kwargs})

# Uso
logger = StructuredLogger('inventario_integration')
logger.info('API call completed', 
           endpoint='/inventory/items', 
           response_time=0.245, 
           status_code=200)
```

## 10. Casos de Uso de Integración

### 10.1 Sincronización de Inventario

#### Sincronización Bidireccional
```python
class InventorySyncService:
    def __init__(self, external_system, inventario_client):
        self.external_system = external_system
        self.inventario_client = inventario_client
    
    def sync_from_external(self):
        """Sincronizar desde sistema externo hacia plataforma"""
        external_items = self.external_system.get_all_items()
        
        for external_item in external_items:
            try:
                # Buscar ítem existente
                existing_item = self.inventario_client.inventory.get_item_by_sku(
                    external_item['sku']
                )
                
                if existing_item:
                    # Actualizar si hay cambios
                    if self.has_changes(existing_item, external_item):
                        self.inventario_client.inventory.update_item(
                            existing_item.id,
                            self.map_external_to_inventario(external_item)
                        )
                else:
                    # Crear nuevo ítem
                    self.inventario_client.inventory.create_item(
                        self.map_external_to_inventario(external_item)
                    )
                    
            except Exception as e:
                logger.error(f"Error syncing item {external_item['sku']}: {e}")
    
    def sync_to_external(self):
        """Sincronizar desde plataforma hacia sistema externo"""
        inventario_items = self.inventario_client.inventory.list_all_items()
        
        for item in inventario_items:
            try:
                external_data = self.map_inventario_to_external(item)
                self.external_system.upsert_item(external_data)
                
            except Exception as e:
                logger.error(f"Error syncing item {item.sku}: {e}")
```

### 10.2 Automatización de Transferencias

#### Auto-Approval basado en Reglas
```python
class TransferAutomationService:
    def __init__(self, inventario_client):
        self.client = inventario_client
        self.rules = self.load_approval_rules()
    
    def process_transfer_request(self, transfer_id):
        transfer = self.client.transfers.get_transfer(transfer_id)
        
        # Evaluar reglas de auto-aprobación
        if self.should_auto_approve(transfer):
            self.client.transfers.approve_transfer(
                transfer_id,
                items_aprobados=self.calculate_approved_quantities(transfer)
            )
            
            logger.info(f"Transfer {transfer.numero_solicitud} auto-approved")
        else:
            # Notificar para revisión manual
            self.notify_manual_review_required(transfer)
    
    def should_auto_approve(self, transfer):
        # Reglas de ejemplo
        rules = [
            transfer.prioridad == 'baja',
            transfer.valor_total < 1000000,  # Menos de $1M
            all(item.cantidad_solicitada <= 10 for item in transfer.items),
            transfer.hidrologica_origen.confiabilidad >= 0.9
        ]
        
        return all(rules)
```

## 11. Testing de Integración

### 11.1 Tests Automatizados

#### Test de API
```python
import pytest
import requests_mock

class TestInventarioIntegration:
    def setup_method(self):
        self.client = InventarioClient(
            base_url="https://api.test.inventario.gov.co/api/v1/",
            client_id="test_client",
            client_secret="test_secret"
        )
    
    @requests_mock.Mocker()
    def test_create_item(self, m):
        # Mock API response
        m.post(
            'https://api.test.inventario.gov.co/api/v1/inventory/items/',
            json={'id': 'test-uuid', 'sku': 'TEST-001'},
            status_code=201
        )
        
        # Test creation
        item = self.client.inventory.create_item({
            'sku': 'TEST-001',
            'nombre': 'Test Item',
            'tipo': 'tuberia'
        })
        
        assert item['sku'] == 'TEST-001'
    
    @requests_mock.Mocker()
    def test_webhook_validation(self, m):
        payload = '{"event": "transfer.approved", "data": {}}'
        signature = 'sha256=test_signature'
        
        is_valid = verify_webhook_signature(
            payload, signature, 'test_secret'
        )
        
        assert is_valid is False  # Should fail with test signature
```

### 11.2 Load Testing

#### Artillery Configuration
```yaml
config:
  target: 'https://api.inventario.gov.co'
  phases:
    - duration: 60
      arrivalRate: 10
  headers:
    Authorization: 'Bearer {{ $randomString() }}'

scenarios:
  - name: "List inventory items"
    weight: 70
    flow:
      - get:
          url: "/api/v1/inventory/items/"
  
  - name: "Create transfer"
    weight: 20
    flow:
      - post:
          url: "/api/v1/transfers/external/"
          json:
            hidrologica_destino_id: "{{ $randomUUID() }}"
            items: []
  
  - name: "Get transfer details"
    weight: 10
    flow:
      - get:
          url: "/api/v1/transfers/external/{{ $randomUUID() }}/"
```

## 12. Troubleshooting

### 12.1 Problemas Comunes

#### Error 401 - Unauthorized
```bash
# Verificar token
curl -X GET https://api.inventario.gov.co/api/v1/auth/verify/ \
  -H "Authorization: Bearer <token>"

# Renovar token si es necesario
curl -X POST https://api.inventario.gov.co/api/v1/auth/token/refresh/ \
  -d '{"refresh": "<refresh_token>"}'
```

#### Error 429 - Rate Limited
```python
# Implementar backoff exponencial
def handle_rate_limit(response):
    if response.status_code == 429:
        retry_after = int(response.headers.get('Retry-After', 60))
        time.sleep(retry_after)
        return True
    return False
```

#### Webhook No Recibido
```python
# Verificar configuración
def test_webhook_endpoint():
    response = requests.post('https://your-system.com/webhooks/test', 
                           json={'test': True})
    return response.status_code == 200
```

### 12.2 Logs de Diagnóstico

#### Habilitar Debug Logging
```python
import logging

# Configurar logging detallado
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('inventario_integration')

# Log de requests HTTP
import http.client as http_client
http_client.HTTPConnection.debuglevel = 1
```

#### Análisis de Performance
```python
import time
from functools import wraps

def measure_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        
        logger.info(f"{func.__name__} took {end - start:.2f} seconds")
        return result
    
    return wrapper

@measure_time
def sync_inventory():
    # Código de sincronización
    pass
```

Esta guía proporciona una base sólida para integrar sistemas externos con la Plataforma de Gestión de Inventario. Para casos específicos o dudas adicionales, consulte la documentación de la API o contacte al equipo de soporte técnico.