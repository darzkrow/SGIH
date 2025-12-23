# Documento de Requerimientos

## Introducción

Plataforma integral para el control de inventario de 16 Hidrológicas autónomas coordinadas por un Ente Rector. El sistema permite la trazabilidad total de activos mediante "Fichas de Vida" del producto, gestionando movimientos internos libres y transferencias inter-empresariales reguladas con órdenes de traspaso digitales.

## Glosario

- **Ente_Rector**: Organización central que coordina las 16 hidrológicas
- **Hidrologica**: Entidad autónoma que gestiona acueductos y mantiene inventario
- **Acueducto**: Unidad operativa dentro de una hidrológica
- **Item_Inventario**: Activo físico (tubería, motor, válvula, químico) con UUID único
- **Ficha_Vida**: Historial completo de movimientos y estados de un ítem
- **Orden_Traspaso**: Documento PDF con QR para transferencias inter-empresariales
- **Movimiento_Interno**: Transferencia entre acueductos de la misma hidrológica
- **Transferencia_Externa**: Movimiento entre diferentes hidrológicas
- **Sistema**: La plataforma completa de gestión de inventario

## Requerimientos

### Requerimiento 1: Gestión de Entidades Organizacionales

**Historia de Usuario:** Como administrador del sistema, quiero gestionar la jerarquía organizacional, para que pueda mantener la estructura de Ente Rector, Hidrológicas y Acueductos.

#### Criterios de Aceptación

1. EL Sistema DEBERÁ mantener un Ente_Rector único que coordine todas las hidrológicas
2. EL Sistema DEBERÁ gestionar exactamente 16 Hidrologicas autónomas
3. CUANDO se cree una Hidrologica, EL Sistema DEBERÁ permitir asociar múltiples Acueductos
4. EL Sistema DEBERÁ asignar identificadores únicos a cada entidad organizacional

### Requerimiento 2: Gestión de Inventario y Trazabilidad

**Historia de Usuario:** Como operador de hidrológica, quiero registrar y rastrear activos, para que pueda mantener control total sobre el inventario.

#### Criterios de Aceptación

1. CUANDO se registre un ítem, EL Sistema DEBERÁ asignar un UUID único y SKU
2. EL Sistema DEBERÁ mantener una Ficha_Vida para cada Item_Inventario
3. CUANDO ocurra cualquier movimiento, EL Sistema DEBERÁ registrar en el historial JSON del ítem
4. EL Sistema DEBERÁ clasificar ítems por tipo (tuberías, motores, válvulas, químicos)
5. EL Sistema DEBERÁ mantener el estado actual de cada ítem (disponible, en tránsito, asignado)

### Requerimiento 3: Multitenencia y Seguridad de Datos

**Historia de Usuario:** Como administrador de hidrológica, quiero acceder solo a mi inventario, para que se mantenga la confidencialidad entre organizaciones.

#### Criterios de Aceptación

1. CUANDO un usuario de Hidrologica acceda al sistema, EL Sistema DEBERÁ mostrar únicamente el inventario de su organización
2. EL Sistema DEBERÁ implementar filtros a nivel de base de datos para aislar datos por hidrológica
3. CUANDO el Ente_Rector use el buscador global, EL Sistema DEBERÁ mostrar vista anonimizada del stock de otras hidrológicas
4. EL Sistema DEBERÁ implementar autenticación JWT y permisos basados en roles (RBAC)

### Requerimiento 4: Movimientos Internos

**Historia de Usuario:** Como operador de hidrológica, quiero mover activos entre mis acueductos, para que pueda redistribuir inventario internamente.

#### Criterios de Aceptación

1. CUANDO se solicite un movimiento entre acueductos de la misma Hidrologica, EL Sistema DEBERÁ permitir transferencia directa
2. CUANDO se ejecute un movimiento interno, EL Sistema DEBERÁ actualizar la ubicación del ítem inmediatamente
3. CUANDO se complete un movimiento interno, EL Sistema DEBERÁ registrar el cambio en la Ficha_Vida del ítem
4. EL Sistema DEBERÁ mantener trazabilidad completa de movimientos internos

### Requerimiento 5: Workflow de Transferencias Externas

**Historia de Usuario:** Como administrador rector, quiero gestionar transferencias entre hidrológicas, para que pueda optimizar la distribución de recursos.

#### Criterios de Aceptación

1. CUANDO una Hidrologica solicite un bien, EL Sistema DEBERÁ crear una solicitud de transferencia
2. CUANDO el Ente_Rector reciba una solicitud, EL Sistema DEBERÁ identificar hidrológicas con stock disponible
3. CUANDO el Ente_Rector autorice una transferencia, EL Sistema DEBERÁ generar automáticamente una Orden_Traspaso
4. EL Sistema DEBERÁ requerir aprobación del Ente_Rector para todas las transferencias externas

### Requerimiento 6: Generación de Órdenes de Traspaso

**Historia de Usuario:** Como operador del sistema, quiero generar órdenes de traspaso digitales, para que pueda documentar transferencias oficialmente.

#### Criterios de Aceptación

1. CUANDO se apruebe una transferencia externa, EL Sistema DEBERÁ generar un PDF único de Orden_Traspaso
2. EL Sistema DEBERÁ incluir un código QR en cada Orden_Traspaso
3. EL Sistema DEBERÁ generar URL firmada digitalmente en el código QR
4. CUANDO se genere una orden, EL Sistema DEBERÁ incluir información completa (origen, destino, material, fechas)

### Requerimiento 7: Validación por Código QR

**Historia de Usuario:** Como punto de control, quiero escanear códigos QR, para que pueda verificar y confirmar transferencias.

#### Criterios de Aceptación

1. CUANDO se escanee un código QR válido, EL Sistema DEBERÁ mostrar el estatus real de la transferencia
2. EL Sistema DEBERÁ validar la autenticidad de la URL firmada en el QR
3. CUANDO se acceda via QR, EL Sistema DEBERÁ mostrar origen, destino, material y firmas digitales
4. EL Sistema DEBERÁ permitir confirmación de recepción/salida via interfaz QR

### Requerimiento 8: Perfiles de Usuario y Interfaces

**Historia de Usuario:** Como usuario del sistema, quiero una interfaz adaptada a mi rol, para que pueda realizar mis tareas eficientemente.

#### Criterios de Aceptación

1. CUANDO un Administrador_Rector acceda, EL Sistema DEBERÁ mostrar vista global con mapas de calor de stock
2. CUANDO un Operador_Hidrologica acceda, EL Sistema DEBERÁ mostrar gestión de stock propio y solicitudes
3. CUANDO un Punto_Control acceda, EL Sistema DEBERÁ mostrar interfaz simplificada para escaneo QR
4. EL Sistema DEBERÁ proporcionar dashboard de indicadores críticos según el rol del usuario

### Requerimiento 9: Arquitectura Contenedorizada

**Historia de Usuario:** Como administrador de sistemas, quiero una aplicación completamente contenedorizada, para que pueda desplegar y mantener el sistema fácilmente.

#### Criterios de Aceptación

1. EL Sistema DEBERÁ ejecutarse completamente en contenedores Docker
2. EL Sistema DEBERÁ incluir servicios para backend Django, frontend, PostgreSQL, Redis y Celery
3. EL Sistema DEBERÁ proporcionar configuración Docker Compose para desarrollo y producción
4. EL Sistema DEBERÁ usar Gunicorn para el backend y Nginx para servir archivos estáticos

### Requerimiento 10: Procesamiento Asíncrono y Notificaciones

**Historia de Usuario:** Como usuario del sistema, quiero recibir notificaciones en tiempo real, para que pueda estar informado de cambios importantes.

#### Criterios de Aceptación

1. CUANDO se generen reportes o PDFs, EL Sistema DEBERÁ procesarlos usando Celery en segundo plano
2. EL Sistema DEBERÁ usar Redis para gestionar notificaciones en tiempo real
3. CUANDO ocurran eventos importantes, EL Sistema DEBERÁ notificar a usuarios relevantes
4. EL Sistema DEBERÁ mantener cola de tareas para procesamiento asíncrono

### Requerimiento 11: Documentación y Migración Inicial

**Historia de Usuario:** Como desarrollador, quiero documentación completa y datos iniciales, para que pueda entender y configurar el sistema.

#### Criterios de Aceptación

1. EL Sistema DEBERÁ proporcionar documentación API usando Swagger/OpenAPI
2. EL Sistema DEBERÁ incluir script de migración con las 16 hidrológicas precargadas
3. EL Sistema DEBERÁ documentar todos los endpoints y modelos de datos
4. EL Sistema DEBERÁ proporcionar ejemplos de uso para cada funcionalidad principal