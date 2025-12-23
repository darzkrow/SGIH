"""
Configuración global de pytest para el proyecto
"""
import os
import django
from django.conf import settings

# Configurar Django antes de importar cualquier cosa
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventory_platform.settings')
django.setup()

import pytest
import uuid
from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.models import EnteRector, Hidrologica, Acueducto
from apps.inventory.models import ItemInventario, CategoriaItem
from apps.transfers.models import TransferenciaExterna

User = get_user_model()


@pytest.fixture(scope='session')
def django_db_setup():
    """Configuración de base de datos para tests"""
    pass


@pytest.fixture
def api_client():
    """Cliente API para tests"""
    return APIClient()


@pytest.fixture
def ente_rector():
    """Fixture para Ente Rector"""
    return EnteRector.objects.create(
        nombre="Ente Rector Test",
        codigo="ERT",
        descripcion="Ente Rector para testing"
    )


@pytest.fixture
def hidrologica_atlantico(ente_rector):
    """Fixture para Hidrológica del Atlántico"""
    return Hidrologica.objects.create(
        ente_rector=ente_rector,
        nombre="Hidrológica del Atlántico Test",
        codigo="HAT",
        descripcion="Hidrológica de prueba",
        direccion="Test Address Barranquilla",
        telefono="+57 1 234 5678",
        email="test@hat.gov.co"
    )


@pytest.fixture
def hidrologica_bolivar(ente_rector):
    """Fixture para Hidrológica de Bolívar"""
    return Hidrologica.objects.create(
        ente_rector=ente_rector,
        nombre="Hidrológica de Bolívar Test",
        codigo="HBL",
        descripcion="Hidrológica de prueba",
        direccion="Test Address Cartagena",
        telefono="+57 2 234 5678",
        email="test@hbl.gov.co"
    )


@pytest.fixture
def acueducto_barranquilla(hidrologica_atlantico):
    """Fixture para Acueducto de Barranquilla"""
    return Acueducto.objects.create(
        hidrologica=hidrologica_atlantico,
        nombre="Acueducto Barranquilla Test",
        codigo="ABT",
        direccion="Test Address Acueducto"
    )


@pytest.fixture
def acueducto_cartagena(hidrologica_bolivar):
    """Fixture para Acueducto de Cartagena"""
    return Acueducto.objects.create(
        hidrologica=hidrologica_bolivar,
        nombre="Acueducto Cartagena Test",
        codigo="ACT",
        direccion="Test Address Acueducto Cartagena"
    )


@pytest.fixture
def acueducto_barranquilla_2(hidrologica_atlantico):
    """Fixture para segundo Acueducto en Hidrológica del Atlántico"""
    return Acueducto.objects.create(
        hidrologica=hidrologica_atlantico,
        nombre="Acueducto Barranquilla 2 Test",
        codigo="AB2T",
        direccion="Test Address Acueducto 2"
    )


@pytest.fixture
def admin_rector_user():
    """Usuario administrador del Ente Rector"""
    return User.objects.create_user(
        username="admin_rector_test",
        email="admin@test.gov.co",
        password="testpass123",
        first_name="Admin",
        last_name="Rector",
        rol="admin_rector",
        hidrologica=None,
        is_staff=True,
        is_superuser=True
    )


@pytest.fixture
def operador_atlantico_user(hidrologica_atlantico):
    """Usuario operador de Hidrológica del Atlántico"""
    return User.objects.create_user(
        username="operador_atlantico_test",
        email="operador@hat.test.gov.co",
        password="testpass123",
        first_name="Operador",
        last_name="Atlántico",
        rol="operador_hidrologica",
        hidrologica=hidrologica_atlantico
    )


@pytest.fixture
def operador_bolivar_user(hidrologica_bolivar):
    """Usuario operador de Hidrológica de Bolívar"""
    return User.objects.create_user(
        username="operador_bolivar_test",
        email="operador@hbl.test.gov.co",
        password="testpass123",
        first_name="Operador",
        last_name="Bolívar",
        rol="operador_hidrologica",
        hidrologica=hidrologica_bolivar
    )


@pytest.fixture
def punto_control_user(hidrologica_atlantico):
    """Usuario punto de control"""
    return User.objects.create_user(
        username="control_test",
        email="control@test.com",
        password="testpass123",
        first_name="Control",
        last_name="Test",
        rol="punto_control",
        hidrologica=hidrologica_atlantico
    )


@pytest.fixture
def categoria_tuberia():
    """Categoría de tubería"""
    return CategoriaItem.objects.create(
        nombre="Tubería Test",
        descripcion="Categoría de tubería para testing",
        tipo_item="tuberia",
        activa=True
    )


@pytest.fixture
def categoria_motor():
    """Categoría de motor"""
    return CategoriaItem.objects.create(
        nombre="Motor Test",
        descripcion="Categoría de motor para testing",
        tipo_item="motor",
        activa=True
    )


@pytest.fixture
def item_tuberia_atlantico(hidrologica_atlantico, acueducto_barranquilla, categoria_tuberia):
    """Ítem de tubería en Hidrológica del Atlántico"""
    return ItemInventario.objects.create(
        sku="TUB-TEST-001",
        tipo="tuberia",
        nombre="Tubería PVC Test 4 pulgadas",
        descripcion="Tubería de prueba",
        estado="disponible",
        hidrologica=hidrologica_atlantico,
        acueducto_actual=acueducto_barranquilla,
        categoria=categoria_tuberia,
        especificaciones={
            "material": "PVC",
            "diametro_pulgadas": 4,
            "longitud_metros": 6
        },
        valor_unitario="25000.00",
        fecha_adquisicion="2024-01-01",
        proveedor="Test Provider",
        numero_factura="TEST-001",
        historial_movimientos=[]  # Inicializar historial vacío
    )


@pytest.fixture
def item_motor_bolivar(hidrologica_bolivar, acueducto_cartagena, categoria_motor):
    """Ítem de motor en Hidrológica de Bolívar"""
    return ItemInventario.objects.create(
        sku="MOT-TEST-001",
        tipo="motor",
        nombre="Motor Test 5HP",
        descripcion="Motor de prueba",
        estado="disponible",
        hidrologica=hidrologica_bolivar,
        acueducto_actual=acueducto_cartagena,
        categoria=categoria_motor,
        especificaciones={
            "potencia_hp": 5,
            "voltaje": 220,
            "rpm": 1750
        },
        valor_unitario="2500000.00",
        fecha_adquisicion="2024-01-01",
        proveedor="Test Motors",
        numero_factura="TEST-002",
        historial_movimientos=[]  # Inicializar historial vacío
    )


@pytest.fixture
def transferencia_externa(hidrologica_atlantico, hidrologica_bolivar, acueducto_barranquilla, 
                         acueducto_cartagena, operador_atlantico_user):
    """Transferencia externa de prueba"""
    return TransferenciaExterna.objects.create(
        hidrologica_origen=hidrologica_atlantico,
        acueducto_origen=acueducto_barranquilla,
        hidrologica_destino=hidrologica_bolivar,
        acueducto_destino=acueducto_cartagena,
        solicitado_por=operador_atlantico_user,
        motivo="Test transfer",
        prioridad="media",
        estado="solicitada"
    )


@pytest.fixture
def authenticated_client_rector(api_client, admin_rector_user):
    """Cliente API autenticado como admin rector"""
    refresh = RefreshToken.for_user(admin_rector_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


@pytest.fixture
def authenticated_client_atlantico(api_client, operador_atlantico_user):
    """Cliente API autenticado como operador del Atlántico"""
    refresh = RefreshToken.for_user(operador_atlantico_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


@pytest.fixture
def authenticated_client_bolivar(api_client, operador_bolivar_user):
    """Cliente API autenticado como operador de Bolívar"""
    refresh = RefreshToken.for_user(operador_bolivar_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


@pytest.fixture
def authenticated_client_control(api_client, punto_control_user):
    """Cliente API autenticado como punto de control"""
    refresh = RefreshToken.for_user(punto_control_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


# Configuración de settings para tests
@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """Permite acceso a la base de datos en todos los tests"""
    pass


@pytest.fixture(autouse=True)
def use_test_cache():
    """Usar cache en memoria para tests"""
    with override_settings(
        CACHES={
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            }
        }
    ):
        yield


@pytest.fixture(autouse=True)
def use_test_celery():
    """Usar Celery en modo eager para tests"""
    with override_settings(
        CELERY_TASK_ALWAYS_EAGER=True,
        CELERY_TASK_EAGER_PROPAGATES=True
    ):
        yield