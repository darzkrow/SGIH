# Guía de Uso de la API - Plataforma de Gestión de Inventario

## Introducción

Esta guía proporciona ejemplos prácticos de uso de la API REST de la Plataforma de Gestión de Inventario para las 16 Hidrológicas. La API está construida con Django REST Framework y utiliza autenticación JWT.

## Configuración Base

### URL Base
```
http://localhost:8000/api/v1/
```

### Autenticación
Todas las peticiones (excepto las públicas) requieren un token JWT en el header:
```
Authorization: Bearer <token>
```

## 1. Autenticación

### 1.1 Obtener Token de Acceso

```bash
curl -X POST http://localhost:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "operador.hat@example.com",
    "password": "password123"
  }'
```

**Respuesta:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440010",
    "username": "operador.hat@example.com",
    "role": "operador_hidrologica",
    "hidrologica": {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "nombre": "Hidrológica del Atlántico",
      "codigo": "HAT"
    }
  }
}
```

### 1.2 Refrescar Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
  }'
```

## 2. Gestión de Inventario

### 2.1 Listar Ítems de Inventario

```bash
curl -X GET "http://localhost:8000/api/v1/inventory/items/" \
  -H "Authorization: Bearer <token>"
```

**Con filtros:**
```bash
curl -X GET "http://localhost:8000/api/v1/inventory/items/?tipo=tuberia&estado=disponible&search=PVC" \
  -H "Authorization: Bearer <token>"
```

**Respuesta:**
```json
{
  "count": 25,
  "next": "http://localhost:8000/api/v1/inventory/items/?page=2",
  "previous": null,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440020",
      "sku": "TUB-PVC-001",
      "nombre": "Tubería PVC 4 pulgadas",
      "tipo": "tuberia",
      "estado": "disponible",
      "cantidad_disponible": 50,
      "ubicacion_actual": "Bodega Principal - Estante A1",
      "valor_unitario": "25000.00",
      "categoria": {
        "id": "550e8400-e29b-41d4-a716-446655440030",
        "nombre": "Tuberías",
        "codigo": "TUB"
      }
    }
  ]
}
```

### 2.2 Crear Ítem de Inventario

```bash
curl -X POST http://localhost:8000/api/v1/inventory/items/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "VAL-001",
    "nombre": "Válvula de Compuerta 6 pulgadas",
    "descripcion": "Válvula de compuerta de hierro fundido",
    "tipo": "valvula",
    "categoria_id": "550e8400-e29b-41d4-a716-446655440031",
    "acueducto_actual_id": "550e8400-e29b-41d4-a716-446655440003",
    "ubicacion_actual": "Bodega Principal - Estante B2",
    "cantidad_disponible": 10,
    "valor_unitario": "150000.00",
    "proveedor": "Válvulas Industriales S.A.",
    "numero_factura": "FAC-2024-001",
    "fecha_compra": "2024-01-15"
  }'
```

### 2.3 Obtener Detalles de un Ítem

```bash
curl -X GET http://localhost:8000/api/v1/inventory/items/550e8400-e29b-41d4-a716-446655440020/ \
  -H "Authorization: Bearer <token>"
```

**Respuesta:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440020",
  "sku": "TUB-PVC-001",
  "nombre": "Tubería PVC 4 pulgadas",
  "descripcion": "Tubería de PVC para conducción de agua potable",
  "tipo": "tuberia",
  "estado": "disponible",
  "categoria": {
    "id": "550e8400-e29b-41d4-a716-446655440030",
    "nombre": "Tuberías",
    "codigo": "TUB"
  },
  "hidrologica": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "nombre": "Hidrológica del Atlántico",
    "codigo": "HAT"
  },
  "acueducto_actual": {
    "id": "550e8400-e29b-41d4-a716-446655440003",
    "nombre": "Acueducto Barranquilla Norte",
    "codigo": "ABN"
  },
  "ubicacion_actual": "Bodega Principal - Estante A1",
  "cantidad_disponible": 50,
  "valor_unitario": "25000.00",
  "proveedor": "Tuberías del Caribe S.A.",
  "numero_factura": "FAC-2024-001",
  "fecha_compra": "2024-01-15",
  "ficha_vida": [
    {
      "fecha": "2024-01-15T10:00:00Z",
      "evento": "creacion",
      "usuario": "admin@hat.gov.co",
      "detalles": {
        "cantidad_inicial": 50,
        "ubicacion": "Bodega Principal - Estante A1"
      }
    }
  ],
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:00:00Z"
}
```

### 2.4 Realizar Movimiento Interno

```bash
curl -X POST http://localhost:8000/api/v1/inventory/items/550e8400-e29b-41d4-a716-446655440020/mover_interno/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "acueducto_destino_id": "550e8400-e29b-41d4-a716-446655440004",
    "motivo": "Mantenimiento programado",
    "observaciones": "Traslado para reparación de red principal"
  }'
```

**Respuesta:**
```json
{
  "success": true,
  "message": "Movimiento interno realizado exitosamente",
  "movimiento_id": "550e8400-e29b-41d4-a716-446655440050",
  "nueva_ubicacion": "Acueducto Barranquilla Sur - Bodega Técnica"
}
```

### 2.5 Cambiar Estado de Ítem

```bash
curl -X POST http://localhost:8000/api/v1/inventory/items/550e8400-e29b-41d4-a716-446655440020/cambiar_estado/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "estado": "en_mantenimiento",
    "observaciones": "Requiere revisión técnica"
  }'
```

### 2.6 Obtener Historial Completo

```bash
curl -X GET http://localhost:8000/api/v1/inventory/items/550e8400-e29b-41d4-a716-446655440020/historial_completo/ \
  -H "Authorization: Bearer <token>"
```

### 2.7 Búsqueda Global (Solo Ente Rector)

```bash
curl -X POST http://localhost:8000/api/v1/inventory/items/busqueda_global/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "tubería PVC",
    "tipo": "tuberia",
    "estado": "disponible",
    "hidrologica_id": "550e8400-e29b-41d4-a716-446655440001"
  }'
```

## 3. Gestión de Transferencias

### 3.1 Solicitar Transferencia Externa

```bash
curl -X POST http://localhost:8000/api/v1/transfers/external/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "hidrologica_destino_id": "550e8400-e29b-41d4-a716-446655440002",
    "acueducto_destino_id": "550e8400-e29b-41d4-a716-446655440005",
    "motivo": "Emergencia por rotura de tubería principal",
    "prioridad": "alta",
    "items": [
      {
        "item_id": "550e8400-e29b-41d4-a716-446655440020",
        "cantidad_solicitada": 10
      },
      {
        "item_id": "550e8400-e29b-41d4-a716-446655440021",
        "cantidad_solicitada": 5
      }
    ]
  }'
```

**Respuesta:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440060",
  "numero_solicitud": "SOL-2024-001",
  "estado": "solicitada",
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
  "motivo": "Emergencia por rotura de tubería principal",
  "prioridad": "alta",
  "items": [
    {
      "item": {
        "id": "550e8400-e29b-41d4-a716-446655440020",
        "sku": "TUB-PVC-001",
        "nombre": "Tubería PVC 4 pulgadas"
      },
      "cantidad_solicitada": 10,
      "cantidad_aprobada": null
    }
  ],
  "created_at": "2024-01-20T14:30:00Z"
}
```

### 3.2 Listar Transferencias

```bash
curl -X GET "http://localhost:8000/api/v1/transfers/external/?estado=solicitada" \
  -H "Authorization: Bearer <token>"
```

### 3.3 Aprobar Transferencia

```bash
curl -X POST http://localhost:8000/api/v1/transfers/external/550e8400-e29b-41d4-a716-446655440060/aprobar/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "observaciones": "Aprobada por emergencia",
    "items_aprobados": [
      {
        "item_transferencia_id": "550e8400-e29b-41d4-a716-446655440070",
        "cantidad_aprobada": 8
      }
    ]
  }'
```

### 3.4 Generar PDF de Orden

```bash
curl -X POST http://localhost:8000/api/v1/transfers/external/550e8400-e29b-41d4-a716-446655440060/generar_pdf/ \
  -H "Authorization: Bearer <token>"
```

**Respuesta:**
```json
{
  "success": true,
  "message": "PDF generado exitosamente",
  "task_id": "550e8400-e29b-41d4-a716-446655440080",
  "pdf_url": "/media/pdfs/orden_traspaso_SOL-2024-001.pdf"
}
```

### 3.5 Descargar PDF

```bash
curl -X GET http://localhost:8000/api/v1/transfers/external/550e8400-e29b-41d4-a716-446655440060/descargar_pdf/ \
  -H "Authorization: Bearer <token>" \
  --output orden_traspaso.pdf
```

### 3.6 Validar QR (Endpoint Público)

```bash
curl -X GET "http://localhost:8000/api/v1/transfers/qr/validate/?token=abc123&signature=def456"
```

**Respuesta:**
```json
{
  "valid": true,
  "transferencia": {
    "numero_solicitud": "SOL-2024-001",
    "estado": "aprobada",
    "hidrologica_origen": "Hidrológica del Atlántico",
    "hidrologica_destino": "Hidrológica de Bolívar",
    "items": [
      {
        "nombre": "Tubería PVC 4 pulgadas",
        "cantidad_aprobada": 8
      }
    ]
  },
  "acciones_disponibles": ["confirmar_salida", "confirmar_recepcion"]
}
```

### 3.7 Confirmar con QR

```bash
curl -X POST http://localhost:8000/api/v1/transfers/qr/confirm/ \
  -H "Content-Type: application/json" \
  -d '{
    "token": "abc123",
    "signature": "def456",
    "accion": "confirmar_salida",
    "observaciones": "Salida confirmada por operador"
  }'
```

## 4. Gestión de Notificaciones

### 4.1 Listar Notificaciones

```bash
curl -X GET http://localhost:8000/api/v1/notifications/ \
  -H "Authorization: Bearer <token>"
```

### 4.2 Marcar como Leída

```bash
curl -X POST http://localhost:8000/api/v1/notifications/550e8400-e29b-41d4-a716-446655440090/marcar_leida/ \
  -H "Authorization: Bearer <token>"
```

### 4.3 Obtener Estadísticas

```bash
curl -X GET http://localhost:8000/api/v1/notifications/estadisticas/ \
  -H "Authorization: Bearer <token>"
```

## 5. Casos de Uso Completos

### 5.1 Flujo Completo de Transferencia Externa

1. **Solicitar transferencia:**
```bash
# Paso 1: Crear solicitud
curl -X POST http://localhost:8000/api/v1/transfers/external/ \
  -H "Authorization: Bearer <token_hidrologica_origen>" \
  -d '{"hidrologica_destino_id": "...", "items": [...]}'
```

2. **Aprobar transferencia (desde hidrológica destino):**
```bash
# Paso 2: Aprobar solicitud
curl -X POST http://localhost:8000/api/v1/transfers/external/{id}/aprobar/ \
  -H "Authorization: Bearer <token_hidrologica_destino>" \
  -d '{"items_aprobados": [...]}'
```

3. **Generar orden PDF:**
```bash
# Paso 3: Generar PDF con QR
curl -X POST http://localhost:8000/api/v1/transfers/external/{id}/generar_pdf/ \
  -H "Authorization: Bearer <token>"
```

4. **Confirmar salida con QR:**
```bash
# Paso 4: Escanear QR y confirmar salida
curl -X POST http://localhost:8000/api/v1/transfers/qr/confirm/ \
  -d '{"token": "...", "accion": "confirmar_salida"}'
```

5. **Confirmar recepción con QR:**
```bash
# Paso 5: Escanear QR y confirmar recepción
curl -X POST http://localhost:8000/api/v1/transfers/qr/confirm/ \
  -d '{"token": "...", "accion": "confirmar_recepcion"}'
```

### 5.2 Flujo de Movimiento Interno

1. **Buscar ítem:**
```bash
curl -X GET "http://localhost:8000/api/v1/inventory/items/?search=TUB-PVC-001" \
  -H "Authorization: Bearer <token>"
```

2. **Realizar movimiento:**
```bash
curl -X POST http://localhost:8000/api/v1/inventory/items/{id}/mover_interno/ \
  -H "Authorization: Bearer <token>" \
  -d '{"acueducto_destino_id": "...", "motivo": "..."}'
```

3. **Verificar historial:**
```bash
curl -X GET http://localhost:8000/api/v1/inventory/items/{id}/historial_completo/ \
  -H "Authorization: Bearer <token>"
```

## 6. Códigos de Error

La API utiliza códigos de error estándar:

### Errores de Inventario (3000-3999)
- `ERR_3000`: Ítem no encontrado
- `ERR_3001`: Ítem ya existe
- `ERR_3002`: Estado de ítem inválido
- `ERR_3005`: Stock insuficiente

### Errores de Transferencias (4000-4999)
- `ERR_4000`: Transferencia no encontrada
- `ERR_4001`: Estado de transferencia inválido
- `ERR_4003`: Transferencia ya aprobada

### Ejemplo de respuesta de error:
```json
{
  "error": {
    "code": "ERR_3000",
    "message": "Ítem de inventario no encontrado",
    "details": {
      "item_id": "550e8400-e29b-41d4-a716-446655440020"
    }
  }
}
```

## 7. Paginación

Todas las listas utilizan paginación estándar:

```json
{
  "count": 100,
  "next": "http://localhost:8000/api/v1/inventory/items/?page=3",
  "previous": "http://localhost:8000/api/v1/inventory/items/?page=1",
  "results": [...]
}
```

## 8. Filtrado y Búsqueda

### Parámetros de consulta comunes:
- `search`: Búsqueda de texto libre
- `ordering`: Ordenamiento (`-created_at`, `nombre`, etc.)
- `page`: Número de página
- `page_size`: Tamaño de página (máximo 100)

### Filtros específicos por endpoint:
- **Inventario**: `tipo`, `estado`, `categoria`, `acueducto_actual`
- **Transferencias**: `estado`, `prioridad`, `hidrologica_origen`, `hidrologica_destino`
- **Notificaciones**: `leida`, `tipo`, `fecha_desde`, `fecha_hasta`

## 9. Documentación Interactiva

La documentación interactiva está disponible en:
- **Swagger UI**: http://localhost:8000/api/docs/
- **Schema JSON**: http://localhost:8000/api/schema/

## 10. Consideraciones de Seguridad

1. **Tokens JWT**: Expiran en 1 hora, usar refresh token para renovar
2. **Multitenencia**: Los datos se filtran automáticamente por hidrológica
3. **Permisos**: Cada endpoint valida permisos según el rol del usuario
4. **QR Codes**: Utilizan firmas digitales HMAC-SHA256 con expiración
5. **HTTPS**: Usar siempre HTTPS en producción

## 11. Límites y Cuotas

- **Paginación**: Máximo 100 elementos por página
- **Búsqueda global**: Máximo 50 resultados
- **Archivos PDF**: Máximo 10MB por archivo
- **Rate limiting**: 1000 requests por hora por usuario