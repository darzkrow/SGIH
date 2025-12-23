from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TransferenciaExternaViewSet, MovimientoInternoViewSet, QRValidationViewSet

router = DefaultRouter()
router.register(r'externas', TransferenciaExternaViewSet)
router.register(r'movimientos-internos', MovimientoInternoViewSet)
router.register(r'qr', QRValidationViewSet, basename='qr-validation')

urlpatterns = [
    path('', include(router.urls)),
]