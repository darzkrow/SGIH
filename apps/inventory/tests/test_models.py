"""
Tests unitarios para modelos del módulo inventory
"""
import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.inventory.models import (
    ItemInventario, CategoriaItem, TipoItem, EstadoItem
)


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.models
class TestCategoriaItemModel:
    """Tests para el modelo CategoriaItem"""
    
    def test_create_categoria_item(self):
        """Test crear categoría de ítem"""
        categoria = CategoriaItem.objects.create(
            nombre="Tubería Test",
            descripcion="Categoría de tubería para testing",
            tipo_item="tuberia"
        )
        
        assert categoria.nombre == "Tubería Test"
        assert categoria.tipo_item == "tuberia"
        assert categoria.activa is True
        assert str(categoria) == "Tubería Test (Tubería)"
    
    def test_categoria_unique_nombre(self):
        """Test que el nombre de categoría sea único"""
        CategoriaItem.objects.create(
            nombre="Tubería",
            descripcion="Test 1",
            tipo_item="tuberia"
        )
        
        with pytest.raises(IntegrityError):
            CategoriaItem.objects.create(
                nombre="Tubería",  # Nombre duplicado
                descripcion="Test 2",
                tipo_item="motor"
            )
    
    def test_categoria_tipo_item_validation(self):
        """Test validación de tipo de ítem"""
        categoria = CategoriaItem(
            nombre="Test",
            descripcion="Test",
            tipo_item="invalid_type"
        )
        
        with pytest.raises(ValidationError):
            categoria.full_clean()


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.models
class TestItemInventarioModel:
    """Tests para el modelo ItemInventario"""
    
    def test_create_item_inventario(self, hidrologica_atlantico, acueducto_barranquilla, categoria_tuberia):
        """Test crear ítem de inventario"""
        item = ItemInventario.objects.create(
            sku="TEST-001",
            tipo="tuberia",
            nombre="Tubería Test",
            descripcion="Tubería de prueba",
            estado="disponible",
            hidrologica=hidrologica_atlantico,
            acueducto_actual=acueducto_barranquilla,
            categoria=categoria_tuberia,
            especificaciones={"material": "PVC", "diametro": 4},
            valor_unitario="25000.00",
            fecha_adquisicion="2024-01-01",
            proveedor="Test Provider",
            numero_factura="TEST-001",
            historial_movimientos=[]  # Agregar historial vacío
        )
        
        assert item.sku == "TEST-001"
        assert item.tipo == "tuberia"
        assert item.estado == "disponible"
        assert item.hidrologica == hidrologica_atlantico
        assert item.acueducto_actual == acueducto_barranquilla
        assert item.valor_unitario == Decimal("25000.00")
        assert str(item) == "TEST-001 - Tubería Test"
    
    def test_item_unique_sku(self, hidrologica_atlantico, acueducto_barranquilla, categoria_tuberia):
        """Test que el SKU sea único"""
        ItemInventario.objects.create(
            sku="TEST-001",
            tipo="tuberia",
            nombre="Item 1",
            descripcion="Item de prueba 1",
            hidrologica=hidrologica_atlantico,
            acueducto_actual=acueducto_barranquilla,
            categoria=categoria_tuberia,
            historial_movimientos=[]
        )
        
        with pytest.raises(ValidationError):
            ItemInventario.objects.create(
                sku="TEST-001",  # SKU duplicado
                tipo="motor",
                nombre="Item 2",
                descripcion="Item de prueba 2",
                hidrologica=hidrologica_atlantico,
                acueducto_actual=acueducto_barranquilla,
                categoria=categoria_tuberia,
                historial_movimientos=[]
            )
    
    def test_item_tipo_validation(self, hidrologica_atlantico, acueducto_barranquilla, categoria_tuberia):
        """Test validación de tipo de ítem"""
        item = ItemInventario(
            sku="TEST-001",
            tipo="invalid_type",
            nombre="Test Item",
            hidrologica=hidrologica_atlantico,
            acueducto_actual=acueducto_barranquilla,
            categoria=categoria_tuberia
        )
        
        with pytest.raises(ValidationError):
            item.full_clean()
    
    def test_item_estado_validation(self, hidrologica_atlantico, acueducto_barranquilla, categoria_tuberia):
        """Test validación de estado de ítem"""
        item = ItemInventario(
            sku="TEST-001",
            tipo="tuberia",
            nombre="Test Item",
            estado="invalid_state",
            hidrologica=hidrologica_atlantico,
            acueducto_actual=acueducto_barranquilla,
            categoria=categoria_tuberia
        )
        
        with pytest.raises(ValidationError):
            item.full_clean()
    
    def test_item_ubicacion_actual_property(self, item_tuberia_atlantico):
        """Test propiedad ubicacion_actual"""
        expected = {
            'hidrologica': item_tuberia_atlantico.hidrologica.nombre,
            'hidrologica_codigo': item_tuberia_atlantico.hidrologica.codigo,
            'acueducto': item_tuberia_atlantico.acueducto_actual.nombre,
            'acueducto_codigo': item_tuberia_atlantico.acueducto_actual.codigo
        }
        assert item_tuberia_atlantico.ubicacion_actual == expected
    
    def test_item_puede_transferirse_property(self, item_tuberia_atlantico):
        """Test propiedad puede_transferirse"""
        # Estado disponible debe permitir transferencia
        item_tuberia_atlantico.estado = "disponible"
        assert item_tuberia_atlantico.puede_transferirse is True
        
        # Estado en_transito no debe permitir transferencia
        item_tuberia_atlantico.estado = "en_transito"
        assert item_tuberia_atlantico.puede_transferirse is False
        
        # Estado dado_baja no debe permitir transferencia
        item_tuberia_atlantico.estado = "dado_baja"
        assert item_tuberia_atlantico.puede_transferirse is False
    
    def test_item_cambiar_estado_method(self, item_tuberia_atlantico, operador_atlantico_user):
        """Test método cambiar_estado"""
        estado_inicial = item_tuberia_atlantico.estado
        
        # Limpiar historial para esta prueba
        item_tuberia_atlantico.historial_movimientos = []
        item_tuberia_atlantico.save(update_fields=['historial_movimientos'])
        
        # Cambiar estado
        item_tuberia_atlantico.cambiar_estado(
            "mantenimiento",
            operador_atlantico_user,
            "Mantenimiento programado"
        )
        
        assert item_tuberia_atlantico.estado == "mantenimiento"
        
        # Verificar que se registró en el historial
        historial = item_tuberia_atlantico.historial_movimientos
        assert len(historial) > 0
        
        # Buscar el evento de cambio de estado
        eventos_cambio = [e for e in historial if e.get("tipo") == "cambio_estado"]
        assert len(eventos_cambio) > 0
        
        ultimo_evento = eventos_cambio[-1]
        
        # Verificar la estructura del evento según el formato real
        assert ultimo_evento["tipo"] == "cambio_estado"
        assert ultimo_evento["observaciones"] == "Mantenimiento programado"
        assert "datos_adicionales" in ultimo_evento
        assert ultimo_evento["datos_adicionales"]["estado_anterior"] == estado_inicial
        assert ultimo_evento["datos_adicionales"]["estado_nuevo"] == "mantenimiento"
        assert ultimo_evento["observaciones"] == "Mantenimiento programado"
    
    def test_item_historial_initialization(self, hidrologica_atlantico, acueducto_barranquilla, 
                                         categoria_tuberia, operador_atlantico_user):
        """Test que se inicialice el historial al crear ítem"""
        item = ItemInventario.objects.create(
            sku="TEST-HIST-001",
            tipo="tuberia",
            nombre="Test Historial",
            descripcion="Test historial item",
            hidrologica=hidrologica_atlantico,
            acueducto_actual=acueducto_barranquilla,
            categoria=categoria_tuberia,
            historial_movimientos=[]  # Inicializar historial vacío
        )
        
        # El historial debe estar inicializado como lista vacía
        assert isinstance(item.historial_movimientos, list)
        assert len(item.historial_movimientos) == 0
    
    def test_item_especificaciones_json_field(self, item_tuberia_atlantico):
        """Test campo JSON especificaciones"""
        especificaciones = {
            "material": "PVC",
            "diametro_pulgadas": 4,
            "presion_trabajo_psi": 200,
            "longitud_metros": 6
        }
        
        item_tuberia_atlantico.especificaciones = especificaciones
        item_tuberia_atlantico.save()
        
        # Recargar desde DB
        item_tuberia_atlantico.refresh_from_db()
        
        assert item_tuberia_atlantico.especificaciones == especificaciones
        assert item_tuberia_atlantico.especificaciones["material"] == "PVC"
        assert item_tuberia_atlantico.especificaciones["diametro_pulgadas"] == 4
    
    def test_item_cascade_delete_hidrologica(self, item_tuberia_atlantico):
        """Test que al eliminar hidrológica se eliminen los ítems"""
        hidrologica = item_tuberia_atlantico.hidrologica
        item_id = item_tuberia_atlantico.id
        
        hidrologica.delete()
        
        assert not ItemInventario.objects.filter(id=item_id).exists()
    
    def test_item_cascade_delete_acueducto(self, item_tuberia_atlantico):
        """Test que al eliminar acueducto se eliminen los ítems"""
        acueducto = item_tuberia_atlantico.acueducto_actual
        item_id = item_tuberia_atlantico.id
        
        acueducto.delete()
        
        assert not ItemInventario.objects.filter(id=item_id).exists()
    
    def test_item_cascade_delete_categoria(self, item_tuberia_atlantico):
        """Test que al eliminar categoría se establezca NULL en el ítem"""
        categoria = item_tuberia_atlantico.categoria
        item_id = item_tuberia_atlantico.id
        
        categoria.delete()
        
        # El ítem debe seguir existiendo pero con categoría NULL
        item = ItemInventario.objects.get(id=item_id)
        assert item.categoria is None