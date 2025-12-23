"""
Tests unitarios para vistas/APIs del módulo inventory
"""
import pytest
import json
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.api
class TestItemInventarioViewSet:
    """Tests para ItemInventarioViewSet"""
    
    def test_list_items_authenticated_user(self, authenticated_client_atlantico, item_tuberia_atlantico):
        """Test listar ítems como usuario autenticado"""
        url = reverse('iteminventario-list')
        response = authenticated_client_atlantico.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert len(response.data['results']) >= 1
        
        # Verificar que solo ve ítems de su hidrológica
        for item in response.data['results']:
            # En un test real, verificaríamos que hidrologica_id coincide
            assert 'sku' in item
            assert 'nombre' in item
    
    def test_list_items_multitenancy_isolation(self, authenticated_client_atlantico, 
                                             authenticated_client_bolivar,
                                             item_tuberia_atlantico, item_motor_bolivar):
        """Test aislamiento de multitenencia en listado"""
        url = reverse('iteminventario-list')
        
        # Usuario del Atlántico
        response_atlantico = authenticated_client_atlantico.get(url)
        items_atlantico = [item['sku'] for item in response_atlantico.data['results']]
        
        # Usuario de Bolívar
        response_bolivar = authenticated_client_bolivar.get(url)
        items_bolivar = [item['sku'] for item in response_bolivar.data['results']]
        
        # Cada usuario debe ver solo sus ítems
        assert item_tuberia_atlantico.sku in items_atlantico
        assert item_motor_bolivar.sku not in items_atlantico
        
        assert item_motor_bolivar.sku in items_bolivar
        assert item_tuberia_atlantico.sku not in items_bolivar
    
    def test_list_items_admin_rector_sees_all(self, authenticated_client_rector,
                                            item_tuberia_atlantico, item_motor_bolivar):
        """Test que admin rector vea todos los ítems"""
        url = reverse('iteminventario-list')
        response = authenticated_client_rector.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        items_skus = [item['sku'] for item in response.data['results']]
        
        # Admin rector debe ver ítems de todas las hidrológicas
        assert item_tuberia_atlantico.sku in items_skus
        assert item_motor_bolivar.sku in items_skus
    
    def test_list_items_with_filters(self, authenticated_client_atlantico, item_tuberia_atlantico):
        """Test filtrado de ítems"""
        url = reverse('iteminventario-list')
        
        # Filtrar por tipo
        response = authenticated_client_atlantico.get(url, {'tipo': 'tuberia'})
        assert response.status_code == status.HTTP_200_OK
        
        for item in response.data['results']:
            assert item['tipo'] == 'tuberia'
        
        # Filtrar por estado
        response = authenticated_client_atlantico.get(url, {'estado': 'disponible'})
        assert response.status_code == status.HTTP_200_OK
        
        for item in response.data['results']:
            assert item['estado'] == 'disponible'
    
    def test_list_items_with_search(self, authenticated_client_atlantico, item_tuberia_atlantico):
        """Test búsqueda de ítems"""
        url = reverse('iteminventario-list')
        
        # Buscar por SKU
        response = authenticated_client_atlantico.get(url, {'search': item_tuberia_atlantico.sku})
        assert response.status_code == status.HTTP_200_OK
        
        items_skus = [item['sku'] for item in response.data['results']]
        assert item_tuberia_atlantico.sku in items_skus
        
        # Buscar por nombre
        response = authenticated_client_atlantico.get(url, {'search': 'Tubería'})
        assert response.status_code == status.HTTP_200_OK
    
    def test_create_item_success(self, authenticated_client_atlantico, categoria_tuberia, acueducto_barranquilla):
        """Test crear ítem exitosamente"""
        url = reverse('iteminventario-list')
        data = {
            'sku': 'NEW-TEST-001',
            'tipo': 'tuberia',
            'nombre': 'Nueva Tubería Test',
            'descripcion': 'Tubería creada en test',
            'estado': 'disponible',
            'categoria': str(categoria_tuberia.id),
            'acueducto_actual': str(acueducto_barranquilla.id),
            'especificaciones': {
                'material': 'PVC',
                'diametro': 6
            },
            'valor_unitario': '30000.00',
            'proveedor': 'Test Provider'
        }
        
        response = authenticated_client_atlantico.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        
        # Verificar datos creados
        assert response.data['sku'] == 'NEW-TEST-001'
        assert response.data['nombre'] == 'Nueva Tubería Test'
        assert response.data['tipo'] == 'tuberia'
    
    def test_create_item_duplicate_sku(self, authenticated_client_atlantico, item_tuberia_atlantico,
                                     categoria_tuberia, acueducto_barranquilla):
        """Test que no permita crear ítem con SKU duplicado"""
        url = reverse('iteminventario-list')
        data = {
            'sku': item_tuberia_atlantico.sku,  # SKU duplicado
            'tipo': 'motor',
            'nombre': 'Motor Test',
            'categoria': str(categoria_tuberia.id),
            'acueducto_actual': str(acueducto_barranquilla.id)
        }
        
        response = authenticated_client_atlantico.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_retrieve_item_success(self, authenticated_client_atlantico, item_tuberia_atlantico):
        """Test obtener detalles de ítem"""
        url = reverse('iteminventario-detail', kwargs={'pk': item_tuberia_atlantico.id})
        response = authenticated_client_atlantico.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(item_tuberia_atlantico.id)
        assert response.data['sku'] == item_tuberia_atlantico.sku
        assert 'historial_movimientos' in response.data
    
    def test_retrieve_item_cross_hidrologica_forbidden(self, authenticated_client_atlantico, item_motor_bolivar):
        """Test que no permita ver ítem de otra hidrológica"""
        url = reverse('iteminventario-detail', kwargs={'pk': item_motor_bolivar.id})
        response = authenticated_client_atlantico.get(url)
        
        # Debe retornar 404 (no encontrado) por multitenencia
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_update_item_success(self, authenticated_client_atlantico, item_tuberia_atlantico):
        """Test actualizar ítem exitosamente"""
        url = reverse('iteminventario-detail', kwargs={'pk': item_tuberia_atlantico.id})
        data = {
            'nombre': 'Tubería Actualizada',
            'descripcion': 'Descripción actualizada'
        }
        
        response = authenticated_client_atlantico.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['nombre'] == 'Tubería Actualizada'
    
    def test_delete_item_success(self, authenticated_client_atlantico, item_tuberia_atlantico):
        """Test eliminar ítem exitosamente"""
        url = reverse('iteminventario-detail', kwargs={'pk': item_tuberia_atlantico.id})
        response = authenticated_client_atlantico.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
    
    def test_mover_interno_action(self, authenticated_client_atlantico, item_tuberia_atlantico, acueducto_cartagena):
        """Test acción de movimiento interno"""
        url = reverse('iteminventario-mover-interno', kwargs={'pk': item_tuberia_atlantico.id})
        data = {
            'acueducto_destino_id': str(acueducto_cartagena.id),
            'motivo': 'Redistribución de inventario',
            'observaciones': 'Movimiento de prueba'
        }
        
        response = authenticated_client_atlantico.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'movimiento_id' in response.data
    
    def test_cambiar_estado_action(self, authenticated_client_atlantico, item_tuberia_atlantico):
        """Test acción de cambio de estado"""
        url = reverse('iteminventario-cambiar-estado', kwargs={'pk': item_tuberia_atlantico.id})
        data = {
            'estado': 'en_mantenimiento',
            'observaciones': 'Mantenimiento programado'
        }
        
        response = authenticated_client_atlantico.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert response.data['estado_nuevo'] == 'en_mantenimiento'
    
    def test_historial_completo_action(self, authenticated_client_atlantico, item_tuberia_atlantico):
        """Test acción de historial completo"""
        url = reverse('iteminventario-historial-completo', kwargs={'pk': item_tuberia_atlantico.id})
        response = authenticated_client_atlantico.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'item' in response.data
        assert 'ficha_vida' in response.data
        assert 'movimientos_internos' in response.data
    
    def test_busqueda_global_admin_rector_only(self, authenticated_client_rector, authenticated_client_atlantico,
                                             item_tuberia_atlantico):
        """Test que búsqueda global solo esté disponible para admin rector"""
        url = reverse('iteminventario-busqueda-global')
        data = {
            'query': 'tubería',
            'tipo': 'tuberia'
        }
        
        # Admin rector debe tener acceso
        response = authenticated_client_rector.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert 'total_encontrados' in response.data
        assert 'items' in response.data
        
        # Operador no debe tener acceso
        response = authenticated_client_atlantico.post(url, data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_estadisticas_action(self, authenticated_client_atlantico, item_tuberia_atlantico):
        """Test acción de estadísticas"""
        url = reverse('iteminventario-estadisticas')
        response = authenticated_client_atlantico.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'total_items' in response.data
        assert 'por_tipo' in response.data
        assert 'por_estado' in response.data
        assert 'valor_total' in response.data
    
    def test_disponibles_para_transferencia_action(self, authenticated_client_atlantico, item_tuberia_atlantico):
        """Test acción de ítems disponibles para transferencia"""
        url = reverse('iteminventario-disponibles-para-transferencia')
        response = authenticated_client_atlantico.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        
        # Verificar que solo incluye ítems disponibles
        for item in response.data:
            assert item['estado'] in ['disponible', 'asignado']
    
    def test_unauthorized_access(self, api_client, item_tuberia_atlantico):
        """Test que requiera autenticación"""
        url = reverse('iteminventario-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_punto_control_read_only_access(self, authenticated_client_control, item_tuberia_atlantico):
        """Test que punto control solo tenga acceso de lectura"""
        # Lectura debe funcionar
        url = reverse('iteminventario-list')
        response = authenticated_client_control.get(url)
        assert response.status_code == status.HTTP_200_OK
        
        # Escritura debe estar prohibida
        url = reverse('iteminventario-list')
        data = {
            'sku': 'CONTROL-TEST',
            'tipo': 'tuberia',
            'nombre': 'Test Control'
        }
        response = authenticated_client_control.post(url, data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.api
class TestCategoriaItemViewSet:
    """Tests para CategoriaItemViewSet"""
    
    def test_list_categorias(self, authenticated_client_atlantico, categoria_tuberia):
        """Test listar categorías"""
        url = reverse('categoriaitem-list')
        response = authenticated_client_atlantico.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1
        
        # Verificar estructura de datos
        categoria = response.data['results'][0]
        assert 'id' in categoria
        assert 'nombre' in categoria
        assert 'tipo_item' in categoria
    
    def test_create_categoria_admin_rector_only(self, authenticated_client_rector, authenticated_client_atlantico):
        """Test que solo admin rector pueda crear categorías"""
        url = reverse('categoriaitem-list')
        data = {
            'nombre': 'Nueva Categoría',
            'descripcion': 'Categoría de prueba',
            'tipo_item': 'valvula'
        }
        
        # Admin rector debe poder crear
        response = authenticated_client_rector.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        
        # Operador no debe poder crear
        data['nombre'] = 'Otra Categoría'
        response = authenticated_client_atlantico.post(url, data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_filter_categorias_by_tipo(self, authenticated_client_atlantico, categoria_tuberia, categoria_motor):
        """Test filtrar categorías por tipo"""
        url = reverse('categoriaitem-list')
        
        # Filtrar por tipo tubería
        response = authenticated_client_atlantico.get(url, {'tipo_item': 'tuberia'})
        assert response.status_code == status.HTTP_200_OK
        
        for categoria in response.data['results']:
            assert categoria['tipo_item'] == 'tuberia'
    
    def test_search_categorias(self, authenticated_client_atlantico, categoria_tuberia):
        """Test búsqueda de categorías"""
        url = reverse('categoriaitem-list')
        response = authenticated_client_atlantico.get(url, {'search': 'Tubería'})
        
        assert response.status_code == status.HTTP_200_OK
        # Debe encontrar la categoría de tubería
        nombres = [cat['nombre'] for cat in response.data['results']]
        assert any('Tubería' in nombre for nombre in nombres)