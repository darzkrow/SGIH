# Guía de Workflows - Plataforma de Gestión de Inventario

## Introducción

Esta guía describe los workflows principales de la Plataforma de Gestión de Inventario, incluyendo los procesos de negocio, estados, transiciones y mejores prácticas para cada tipo de operación.

## 1. Workflow de Transferencias Externas

### 1.1 Estados del Workflow

```
SOLICITADA → APROBADA → ORDEN_GENERADA → EN_TRANSITO → COMPLETADA
     ↓           ↓
  RECHAZADA   CANCELADA
```

### 1.2 Proceso Completo

#### Fase 1: Solicitud (Hidrológica Origen)
1. **Identificar necesidad**: El operador identifica la necesidad de ítems
2. **Buscar disponibilidad**: Verificar stock en otras hidrológicas
3. **Crear solicitud**: Especificar ítems, cantidades y justificación
4. **Envío automático**: El sistema notifica a la hidrológica destino

**Actores**: Operador Hidrológica Origen
**Estado**: `SOLICITADA`

#### Fase 2: Evaluación (Hidrológica Destino)
1. **Recibir notificación**: Revisar solicitud entrante
2. **Verificar disponibilidad**: Confirmar stock disponible
3. **Evaluar justificación**: Revisar motivo y prioridad
4. **Tomar decisión**: Aprobar, rechazar o solicitar modificaciones

**Actores**: Operador Hidrológica Destino
**Estados posibles**: `APROBADA`, `RECHAZADA`

#### Fase 3: Preparación (Hidrológica Destino)
1. **Generar orden**: Crear PDF con QR code único
2. **Preparar ítems**: Separar y embalar ítems aprobados
3. **Actualizar inventario**: Marcar ítems como "reservados"
4. **Notificar preparación**: Informar que está listo para recoger

**Actores**: Operador Hidrológica Destino
**Estado**: `ORDEN_GENERADA`

#### Fase 4: Transporte (Ambas Hidrológicas)
1. **Confirmar salida**: Escanear QR al momento de la salida
2. **Actualizar estado**: Sistema marca como "en tránsito"
3. **Tracking**: Seguimiento del envío (opcional)
4. **Confirmar recepción**: Escanear QR al recibir

**Actores**: Operadores de ambas hidrológicas
**Estados**: `EN_TRANSITO` → `COMPLETADA`

### 1.3 Reglas de Negocio

#### Validaciones de Solicitud
- Solo se pueden solicitar ítems disponibles
- La cantidad no puede exceder el stock disponible
- Debe especificarse un motivo válido
- La hidrológica origen y destino deben ser diferentes

#### Validaciones de Aprobación
- Solo la hidrológica destino puede aprobar/rechazar
- La cantidad aprobada no puede exceder la solicitada
- Se debe verificar stock al momento de aprobar
- Se requiere justificación para rechazos

#### Validaciones de QR
- Cada QR tiene una firma digital única
- Los QR expiran después de 7 días
- Solo se puede usar cada QR una vez por acción
- Las acciones deben seguir el orden: salida → recepción

### 1.4 Notificaciones Automáticas

| Evento | Destinatario | Mensaje |
|--------|--------------|---------|
| Solicitud creada | Hidrológica destino | "Nueva solicitud de transferencia recibida" |
| Solicitud aprobada | Hidrológica origen | "Su solicitud ha sido aprobada" |
| Solicitud rechazada | Hidrológica origen | "Su solicitud ha sido rechazada" |
| Orden generada | Ambas hidrológicas | "Orden de traspaso generada" |
| Salida confirmada | Hidrológica destino | "Ítems han salido de origen" |
| Recepción confirmada | Hidrológica origen | "Ítems recibidos exitosamente" |

## 2. Workflow de Movimientos Internos

### 2.1 Estados del Workflow

```
SOLICITADO → EN_PROCESO → COMPLETADO
     ↓
  CANCELADO
```

### 2.2 Proceso Completo

#### Fase 1: Solicitud
1. **Identificar necesidad**: Necesidad de mover ítem entre acueductos
2. **Verificar permisos**: Confirmar que el usuario puede mover el ítem
3. **Especificar destino**: Seleccionar acueducto destino
4. **Crear movimiento**: Registrar motivo y observaciones

#### Fase 2: Ejecución
1. **Actualizar ubicación**: Cambiar ubicación física del ítem
2. **Registrar en historial**: Agregar evento a la Ficha de Vida
3. **Notificar cambio**: Informar a usuarios relevantes
4. **Completar movimiento**: Marcar como completado

### 2.3 Reglas de Negocio

- Solo se pueden mover ítems dentro de la misma hidrológica
- El ítem debe estar en estado "disponible"
- Se debe especificar un motivo válido
- La ubicación destino debe ser diferente a la origen
- Se registra automáticamente en el historial del ítem

## 3. Workflow de Gestión de Estados

### 3.1 Estados de Ítems

```
DISPONIBLE ⟷ EN_USO ⟷ EN_MANTENIMIENTO
    ↓           ↓            ↓
 RESERVADO   DAÑADO      OBSOLETO
    ↓           ↓            ↓
DISPONIBLE   DADO_BAJA   DADO_BAJA
```

### 3.2 Transiciones Permitidas

| Estado Actual | Estados Permitidos | Requiere Justificación |
|---------------|-------------------|----------------------|
| DISPONIBLE | EN_USO, RESERVADO, EN_MANTENIMIENTO | No |
| EN_USO | DISPONIBLE, DAÑADO, EN_MANTENIMIENTO | Sí |
| RESERVADO | DISPONIBLE, EN_USO | No |
| EN_MANTENIMIENTO | DISPONIBLE, DAÑADO, OBSOLETO | Sí |
| DAÑADO | EN_MANTENIMIENTO, DADO_BAJA | Sí |
| OBSOLETO | DADO_BAJA | Sí |
| DADO_BAJA | (Final) | N/A |

### 3.3 Reglas de Cambio de Estado

#### Automáticas
- `DISPONIBLE` → `RESERVADO`: Al aprobar transferencia externa
- `RESERVADO` → `EN_USO`: Al confirmar salida en transferencia
- `EN_USO` → `DISPONIBLE`: Al confirmar recepción en transferencia

#### Manuales
- Requieren intervención del operador
- Deben incluir observaciones
- Se registran en el historial del ítem
- Pueden requerir aprobación adicional

## 4. Workflow de Notificaciones

### 4.1 Tipos de Notificaciones

#### Por Prioridad
- **ALTA**: Emergencias, rechazos, errores críticos
- **MEDIA**: Aprobaciones, completaciones, cambios de estado
- **BAJA**: Recordatorios, estadísticas, informes

#### Por Canal
- **SISTEMA**: Notificaciones en la aplicación
- **EMAIL**: Correos electrónicos (configurables)
- **SMS**: Mensajes de texto (para emergencias)

### 4.2 Reglas de Envío

#### Destinatarios por Rol
- **Ente Rector**: Todas las notificaciones (vista agregada)
- **Operador Hidrológica**: Notificaciones de su hidrológica
- **Punto Control**: Notificaciones de QR y validaciones

#### Frecuencia
- **Inmediatas**: Emergencias, aprobaciones, rechazos
- **Agrupadas**: Estadísticas diarias, resúmenes semanales
- **Bajo demanda**: Reportes personalizados

## 5. Workflow de Trazabilidad (Ficha de Vida)

### 5.1 Eventos Registrados

#### Eventos de Ciclo de Vida
```json
{
  "evento": "creacion",
  "fecha": "2024-01-15T10:00:00Z",
  "usuario": "admin@hat.gov.co",
  "detalles": {
    "cantidad_inicial": 50,
    "ubicacion": "Bodega Principal",
    "proveedor": "Tuberías del Caribe S.A."
  }
}
```

#### Eventos de Movimiento
```json
{
  "evento": "movimiento_interno",
  "fecha": "2024-01-20T14:30:00Z",
  "usuario": "operador@hat.gov.co",
  "detalles": {
    "acueducto_origen": "Acueducto Norte",
    "acueducto_destino": "Acueducto Sur",
    "motivo": "Mantenimiento programado",
    "cantidad_movida": 10
  }
}
```

#### Eventos de Transferencia
```json
{
  "evento": "transferencia_externa",
  "fecha": "2024-01-25T09:15:00Z",
  "usuario": "operador@hbl.gov.co",
  "detalles": {
    "hidrologica_origen": "HAT",
    "hidrologica_destino": "HBL",
    "numero_solicitud": "SOL-2024-001",
    "cantidad_transferida": 5,
    "estado": "completada"
  }
}
```

### 5.2 Consulta de Historial

#### Por Ítem Individual
- Historial completo de un ítem específico
- Ordenado cronológicamente
- Incluye todos los eventos y cambios

#### Por Lote o Categoría
- Historial agregado de múltiples ítems
- Filtros por fecha, tipo de evento, usuario
- Estadísticas y métricas

#### Reportes de Auditoría
- Trazabilidad completa para auditorías
- Exportación a PDF/Excel
- Firmas digitales para integridad

## 6. Workflow de Validación QR

### 6.1 Generación de QR

```
Transferencia Aprobada
        ↓
Generar Token Único
        ↓
Crear Firma Digital (HMAC-SHA256)
        ↓
Generar QR Code
        ↓
Incluir en PDF de Orden
```

### 6.2 Validación de QR

```
Escanear QR Code
        ↓
Extraer Token y Firma
        ↓
Validar Firma Digital
        ↓
Verificar Expiración
        ↓
Mostrar Información de Transferencia
        ↓
Permitir Acciones (Confirmar Salida/Recepción)
```

### 6.3 Seguridad del QR

#### Elementos de Seguridad
- **Token único**: UUID generado aleatoriamente
- **Firma digital**: HMAC-SHA256 con clave secreta
- **Timestamp**: Fecha de generación para expiración
- **Checksum**: Validación de integridad

#### Validaciones
- Firma digital válida
- Token no expirado (7 días)
- Token no utilizado previamente
- Transferencia en estado válido

## 7. Mejores Prácticas

### 7.1 Para Operadores

#### Solicitudes de Transferencia
- Verificar stock local antes de solicitar
- Proporcionar justificación clara y detallada
- Especificar prioridad correctamente
- Revisar cantidades antes de enviar

#### Aprobaciones
- Verificar disponibilidad real antes de aprobar
- Considerar impacto en operaciones locales
- Comunicar cambios o condiciones especiales
- Aprobar/rechazar en tiempo oportuno

#### Movimientos Internos
- Actualizar ubicaciones físicas inmediatamente
- Registrar observaciones detalladas
- Verificar estado del ítem antes de mover
- Coordinar con personal de campo

### 7.2 Para Administradores

#### Configuración del Sistema
- Mantener datos organizacionales actualizados
- Configurar plantillas de notificación apropiadas
- Establecer políticas de retención de datos
- Monitorear performance y uso del sistema

#### Gestión de Usuarios
- Asignar roles apropiados según responsabilidades
- Revisar permisos periódicamente
- Capacitar usuarios en workflows
- Mantener información de contacto actualizada

### 7.3 Para Auditoría

#### Trazabilidad
- Revisar historiales de ítems críticos regularmente
- Verificar integridad de firmas digitales
- Validar cumplimiento de políticas
- Generar reportes de auditoría periódicos

#### Seguridad
- Monitorear accesos no autorizados
- Verificar uso apropiado de QR codes
- Revisar logs de sistema regularmente
- Mantener backups de datos críticos

## 8. Resolución de Problemas

### 8.1 Problemas Comunes

#### Transferencias Bloqueadas
- **Síntoma**: No se puede aprobar transferencia
- **Causa**: Stock insuficiente o ítem reservado
- **Solución**: Verificar disponibilidad real, liberar reservas

#### QR No Válido
- **Síntoma**: Error al escanear QR
- **Causa**: QR expirado o firma inválida
- **Solución**: Regenerar orden, verificar configuración

#### Notificaciones No Recibidas
- **Síntoma**: No llegan notificaciones
- **Causa**: Configuración de canal incorrecta
- **Solución**: Verificar configuración de usuario y canales

### 8.2 Escalación

#### Nivel 1: Operador Local
- Problemas de uso básico
- Errores de validación
- Consultas de procedimiento

#### Nivel 2: Administrador Hidrológica
- Problemas de configuración
- Errores de permisos
- Problemas de integración

#### Nivel 3: Soporte Técnico
- Errores de sistema
- Problemas de performance
- Fallas de infraestructura

## 9. Métricas y KPIs

### 9.1 Métricas Operacionales

#### Transferencias
- Tiempo promedio de aprobación
- Porcentaje de solicitudes aprobadas
- Tiempo de completación de transferencias
- Número de transferencias por hidrológica

#### Inventario
- Rotación de inventario
- Ítems en cada estado
- Movimientos internos por período
- Valor total de inventario

#### Sistema
- Tiempo de respuesta de API
- Disponibilidad del sistema
- Número de usuarios activos
- Volumen de notificaciones

### 9.2 Reportes Automáticos

#### Diarios
- Resumen de actividades del día
- Transferencias pendientes
- Alertas de stock bajo
- Errores del sistema

#### Semanales
- Estadísticas de transferencias
- Uso del sistema por hidrológica
- Métricas de performance
- Resumen de notificaciones

#### Mensuales
- Análisis de tendencias
- Reportes de auditoría
- Métricas de satisfacción
- Planificación de capacidad