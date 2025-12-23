
# Reporte de Tests - Plataforma de Gestión de Inventario

## Fecha: 2025-12-23 00:11:41

## Resumen de Ejecución:
..........................FFFFFFF......F...F..FF..........F..F...F..EEEF [ 33%]
..FF..EEEFEEEEEEEEEEEEEEEEEEEEEEEEFEEEEEEEEEEEEE.F..F..FFFFFFFF..FF..FFF [ 66%]
FFFFFFFFFFFFFFF...FFFFFEEEEEEEEFFFFFEFFEFFFFFFFFFE.FFEEFFF.FFEEE.EFEEE.E [100%]
=========================== short test summary info ============================
FAILED apps/core/tests/test_middleware.py::TestMultiTenantMiddleware::test_sets_tenant_context_for_authenticated_user
FAILED apps/core/tests/test_middleware.py::TestMultiTenantMiddleware::test_no_tenant_context_for_admin_rector
FAILED apps/core/tests/test_middleware.py::TestMultiTenantMiddleware::test_no_tenant_context_for_anonymous_user
FAILED apps/core/tests/test_middleware.py::TestMultiTenantMiddleware::test_clears_context_after_request
FAILED apps/core/tests/test_middleware.py::TestTenantAccessMiddleware::test_allows_access_to_own_hidrologica_data
FAILED apps/core/tests/test_middleware.py::TestTenantAccessMiddleware::test_allows_admin_rector_access_to_all_data
FAILED apps/core/tests/test_middleware.py::TestTenantAccessMiddleware::test_blocks_cross_hidrologica_access
FAILED apps/core/tests/test_models.py::TestHidrologicaModel::test_hidrologica_unique_codigo
FAILED apps/core/tests/test_models.py::TestUserModel::test_create_admin_rector_user
FAILED apps/core/tests/test_models.py::TestUserModel::test_user_unique_username
FAILED apps/core/tests/test_models.py::TestUserModel::test_user_unique_email
FAILED apps/core/tests/test_permissions.py::TestIsOperadorHidrologicaPermission::test_admin_rector_has_permission
FAILED apps/core/tests/test_permissions.py::TestIsPuntoControlPermission::test_admin_rector_has_permission
FAILED apps/core/tests/test_permissions.py::TestInventoryPermissions::test_punto_control_read_only
FAILED apps/inventory/tests/test_models.py::TestCategoriaItemModel::test_create_categoria_item
FAILED apps/inventory/tests/test_models.py::TestItemInventarioModel::test_create_item_inventario
FAILED apps/inventory/tests/test_models.py::TestItemInventarioModel::test_item_unique_sku
FAILED apps/inventory/tests/test_models.py::TestItemInventarioModel::test_item_historial_initialization
FAILED apps/inventory/tests/test_views.py::TestItemInventarioViewSet::test_create_item_success
FAILED apps/inventory/tests/test_views.py::TestCategoriaItemViewSet::test_create_categoria_admin_rector_only
FAILED apps/notifications/tests/test_models.py::TestPlantillaNotificacionModel::test_create_plantilla_notificacion
FAILED apps/notifications/tests/test_models.py::TestPlantillaNotificacionModel::test_plantilla_render_titulo
FAILED apps/notifications/tests/test_models.py::TestPlantillaNotificacionModel::test_plantilla_render_mensaje
FAILED apps/notifications/tests/test_models.py::TestPlantillaNotificacionModel::test_plantilla_render_with_missing_variables
FAILED apps/notifications/tests/test_models.py::TestCanalNotificacionModel::test_create_canal_notificacion
FAILED apps/notifications/tests/test_models.py::TestCanalNotificacionModel::test_canal_tipo_validation
FAILED apps/notifications/tests/test_models.py::TestCanalNotificacionModel::test_canal_unique_per_user_and_type
FAILED apps/notifications/tests/test_models.py::TestCanalNotificacionModel::test_canal_configuracion_json_field
FAILED apps/notifications/tests/test_models.py::TestNotificacionModel::test_create_notificacion
FAILED apps/notifications/tests/test_models.py::TestNotificacionModel::test_notificacion_marcar_leida_method
FAILED apps/notifications/tests/test_models.py::TestNotificacionModel::test_notificacion_es_reciente_property
FAILED apps/notifications/tests/test_services.py::TestNotificationService::test_crear_notificacion_simple
FAILED apps/notifications/tests/test_services.py::TestNotificationService::test_crear_notificacion_con_plantilla
FAILED apps/notifications/tests/test_services.py::TestNotificationService::test_crear_notificacion_plantilla_no_existe
FAILED apps/notifications/tests/test_services.py::TestNotificationService::test_enviar_notificacion_multiple_usuarios
FAILED apps/notifications/tests/test_services.py::TestNotificationService::test_enviar_notificacion_por_rol
FAILED apps/notifications/tests/test_services.py::TestNotificationService::test_enviar_notificacion_por_hidrologica
FAILED apps/notifications/tests/test_services.py::TestNotificationService::test_marcar_notificacion_leida
FAILED apps/notifications/tests/test_services.py::TestNotificationService::test_marcar_notificacion_leida_usuario_incorrecto
FAILED apps/notifications/tests/test_services.py::TestNotificationService::test_marcar_todas_leidas
FAILED apps/notifications/tests/test_services.py::TestNotificationService::test_obtener_notificaciones_no_leidas
FAILED apps/notifications/tests/test_services.py::TestNotificationService::test_obtener_estadisticas_usuario
FAILED apps/notifications/tests/test_services.py::TestNotificationService::test_limpiar_notificaciones_antiguas
FAILED apps/notifications/tests/test_services.py::TestNotificationService::test_obtener_notificaciones_tiempo_real
FAILED apps/notifications/tests/test_services.py::TestNotificationService::test_publicar_notificacion_tiempo_real
FAILED apps/notifications/tests/test_services.py::TestNotificationService::test_configurar_canal_notificacion
FAILED apps/notifications/tests/test_services.py::TestNotificationService::test_configurar_canal_notificacion_actualizar_existente
FAILED apps/notifications/tests/test_services.py::TestNotificationService::test_obtener_canales_usuario
FAILED apps/transfers/tests/test_models.py::TestTransferenciaExternaModel::test_create_transferencia_externa
FAILED apps/transfers/tests/test_models.py::TestTransferenciaExternaModel::test_transferencia_rechazar_method
FAILED apps/transfers/tests/test_models.py::TestTransferenciaExternaModel::test_transferencia_iniciar_transito_method
FAILED apps/transfers/tests/test_models.py::TestTransferenciaExternaModel::test_transferencia_completar_method
FAILED apps/transfers/tests/test_models.py::TestTransferenciaExternaModel::test_transferencia_invalid_state_transitions
FAILED apps/transfers/tests/test_models.py::TestTransferenciaExternaModel::test_transferencia_puede_cancelarse_property
FAILED apps/transfers/tests/test_qr_service.py::TestQRService::test_generar_token_qr
FAILED apps/transfers/tests/test_qr_service.py::TestQRService::test_validar_token_qr_valid
FAILED apps/transfers/tests/test_qr_service.py::TestQRService::test_validar_token_qr_invalid_signature
FAILED apps/transfers/tests/test_qr_service.py::TestQRService::test_validar_token_qr_expired
FAILED apps/transfers/tests/test_qr_service.py::TestQRService::test_validar_token_qr_malformed
FAILED apps/transfers/tests/test_qr_service.py::TestQRService::test_obtener_info_transferencia_qr_invalid_token
FAILED apps/transfers/tests/test_qr_service.py::TestQRService::test_confirmar_accion_qr_salida
FAILED apps/transfers/tests/test_qr_service.py::TestQRService::test_confirmar_accion_qr_invalid_token
FAILED apps/transfers/tests/test_qr_service.py::TestQRService::test_confirmar_accion_qr_invalid_action
FAILED apps/transfers/tests/test_qr_service.py::TestQRService::test_confirmar_accion_qr_wrong_state
FAILED apps/transfers/tests/test_qr_service.py::TestQRService::test_confirmar_accion_qr_wrong_user
FAILED apps/transfers/tests/test_qr_service.py::TestQRService::test_generar_qr_code_image
FAILED apps/transfers/tests/test_qr_service.py::TestQRService::test_obtener_acciones_disponibles_solicitada
FAILED apps/transfers/tests/test_qr_service.py::TestQRService::test_obtener_acciones_disponibles_aprobada
FAILED apps/transfers/tests/test_qr_service.py::TestQRService::test_obtener_acciones_disponibles_en_transito
FAILED apps/transfers/tests/test_qr_service.py::TestQRService::test_obtener_acciones_disponibles_completada
FAILED apps/transfers/tests/test_services.py::TestTransferService::test_solicitar_transferencia_same_hidrologica
FAILED apps/transfers/tests/test_services.py::TestTransferService::test_solicitar_transferencia_usuario_wrong_hidrologica
FAILED apps/transfers/tests/test_services.py::TestTransferService::test_aprobar_transferencia_not_found
FAILED apps/transfers/tests/test_services.py::TestTransferService::test_aprobar_transferencia_not_ente_rector
FAILED apps/transfers/tests/test_services.py::TestTransferService::test_aprobar_transferencia_wrong_state
FAILED apps/transfers/tests/test_services.py::TestTransferService::test_iniciar_transito_success
FAILED apps/transfers/tests/test_services.py::TestTransferService::test_iniciar_transito_wrong_hidrologica
FAILED apps/transfers/tests/test_services.py::TestMovimientoInternoService::test_crear_movimiento_interno_item_not_found
ERROR apps/core/tests/test_permissions.py::TestMultiTenantPermission::test_object_permission_same_hidrologica
ERROR apps/core/tests/test_permissions.py::TestMultiTenantPermission::test_object_permission_different_hidrologica
ERROR apps/core/tests/test_permissions.py::TestMultiTenantPermission::test_admin_rector_object_permission
ERROR apps/inventory/tests/test_models.py::TestItemInventarioModel::test_item_ubicacion_actual_property
ERROR apps/inventory/tests/test_models.py::TestItemInventarioModel::test_item_puede_transferirse_property
ERROR apps/inventory/tests/test_models.py::TestItemInventarioModel::test_item_cambiar_estado_method
ERROR apps/inventory/tests/test_models.py::TestItemInventarioModel::test_item_especificaciones_json_field
ERROR apps/inventory/tests/test_models.py::TestItemInventarioModel::test_item_cascade_delete_hidrologica
ERROR apps/inventory/tests/test_models.py::TestItemInventarioModel::test_item_cascade_delete_acueducto
ERROR apps/inventory/tests/test_models.py::TestItemInventarioModel::test_item_cascade_delete_categoria
ERROR apps/inventory/tests/test_services.py::TestInventoryService::test_cambiar_estado_item
ERROR apps/inventory/tests/test_services.py::TestInventoryService::test_cambiar_estado_item_mismo_estado
ERROR apps/inventory/tests/test_services.py::TestInventoryService::test_cambiar_estado_item_transicion_invalida
ERROR apps/inventory/tests/test_services.py::TestInventoryService::test_obtener_estadisticas_hidrologica
ERROR apps/inventory/tests/test_services.py::TestInventoryService::test_buscar_items_disponibles
ERROR apps/inventory/tests/test_services.py::TestInventoryService::test_validar_disponibilidad_transferencia
ERROR apps/inventory/tests/test_services.py::TestItemHistoryService::test_registrar_creacion
ERROR apps/inventory/tests/test_services.py::TestItemHistoryService::test_registrar_cambio_estado
ERROR apps/inventory/tests/test_services.py::TestItemHistoryService::test_registrar_movimiento_interno
ERROR apps/inventory/tests/test_services.py::TestItemHistoryService::test_registrar_transferencia_externa
ERROR apps/inventory/tests/test_services.py::TestItemHistoryService::test_registrar_mantenimiento
ERROR apps/inventory/tests/test_services.py::TestItemHistoryService::test_obtener_historial_completo
ERROR apps/inventory/tests/test_services.py::TestItemHistoryService::test_obtener_historial_por_tipo
ERROR apps/inventory/tests/test_services.py::TestItemHistoryService::test_obtener_historial_por_usuario
ERROR apps/inventory/tests/test_services.py::TestItemHistoryService::test_generar_reporte_trazabilidad
ERROR apps/inventory/tests/test_views.py::TestItemInventarioViewSet::test_list_items_authenticated_user
ERROR apps/inventory/tests/test_views.py::TestItemInventarioViewSet::test_list_items_multitenancy_isolation
ERROR apps/inventory/tests/test_views.py::TestItemInventarioViewSet::test_list_items_admin_rector_sees_all
ERROR apps/inventory/tests/test_views.py::TestItemInventarioViewSet::test_list_items_with_filters
ERROR apps/inventory/tests/test_views.py::TestItemInventarioViewSet::test_list_items_with_search
ERROR apps/inventory/tests/test_views.py::TestItemInventarioViewSet::test_create_item_duplicate_sku
ERROR apps/inventory/tests/test_views.py::TestItemInventarioViewSet::test_retrieve_item_success
ERROR apps/inventory/tests/test_views.py::TestItemInventarioViewSet::test_retrieve_item_cross_hidrologica_forbidden
ERROR apps/inventory/tests/test_views.py::TestItemInventarioViewSet::test_update_item_success
ERROR apps/inventory/tests/test_views.py::TestItemInventarioViewSet::test_delete_item_success
ERROR apps/inventory/tests/test_views.py::TestItemInventarioViewSet::test_mover_interno_action
ERROR apps/inventory/tests/test_views.py::TestItemInventarioViewSet::test_cambiar_estado_action
ERROR apps/inventory/tests/test_views.py::TestItemInventarioViewSet::test_historial_completo_action
ERROR apps/inventory/tests/test_views.py::TestItemInventarioViewSet::test_busqueda_global_admin_rector_only
ERROR apps/inventory/tests/test_views.py::TestItemInventarioViewSet::test_estadisticas_action
ERROR apps/inventory/tests/test_views.py::TestItemInventarioViewSet::test_disponibles_para_transferencia_action
ERROR apps/inventory/tests/test_views.py::TestItemInventarioViewSet::test_unauthorized_access
ERROR apps/inventory/tests/test_views.py::TestItemInventarioViewSet::test_punto_control_read_only_access
ERROR apps/transfers/tests/test_models.py::TestItemTransferenciaModel::test_create_item_transferencia
ERROR apps/transfers/tests/test_models.py::TestItemTransferenciaModel::test_item_transferencia_unique_per_transfer
ERROR apps/transfers/tests/test_models.py::TestItemTransferenciaModel::test_item_transferencia_cantidad_validation
ERROR apps/transfers/tests/test_models.py::TestItemTransferenciaModel::test_item_transferencia_cantidad_aprobada_validation
ERROR apps/transfers/tests/test_models.py::TestMovimientoInternoModel::test_create_movimiento_interno
ERROR apps/transfers/tests/test_models.py::TestMovimientoInternoModel::test_movimiento_interno_same_acueducto_validation
ERROR apps/transfers/tests/test_models.py::TestMovimientoInternoModel::test_movimiento_interno_different_hidrologica_validation
ERROR apps/transfers/tests/test_models.py::TestMovimientoInternoModel::test_movimiento_interno_cascade_delete
ERROR apps/transfers/tests/test_qr_service.py::TestQRService::test_obtener_info_transferencia_qr
ERROR apps/transfers/tests/test_qr_service.py::TestQRService::test_confirmar_accion_qr_recepcion
ERROR apps/transfers/tests/test_services.py::TestTransferService::test_solicitar_transferencia_success
ERROR apps/transfers/tests/test_services.py::TestTransferService::test_solicitar_transferencia_item_not_available
ERROR apps/transfers/tests/test_services.py::TestTransferService::test_aprobar_transferencia_success
ERROR apps/transfers/tests/test_services.py::TestTransferService::test_completar_transferencia_success
ERROR apps/transfers/tests/test_services.py::TestTransferService::test_buscar_stock_disponible
ERROR apps/transfers/tests/test_services.py::TestTransferService::test_buscar_stock_disponible_exclude_hidrologica
ERROR apps/transfers/tests/test_services.py::TestMovimientoInternoService::test_crear_movimiento_interno_success
ERROR apps/transfers/tests/test_services.py::TestMovimientoInternoService::test_crear_movimiento_interno_wrong_hidrologica
ERROR apps/transfers/tests/test_services.py::TestMovimientoInternoService::test_crear_movimiento_interno_same_acueducto
ERROR apps/transfers/tests/test_services.py::TestMovimientoInternoService::test_crear_movimiento_interno_item_not_available
ERROR apps/transfers/tests/test_services.py::TestMovimientoInternoService::test_obtener_historial_item
78 failed, 74 passed, 56 warnings, 64 errors in 24.10s


## Estadísticas:
- Tests ejecutados: 78
- Tests exitosos: 0
- Tests fallidos: 78

## Estado General: ❌ CON ERRORES
