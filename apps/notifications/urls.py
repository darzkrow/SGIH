"""
URLs para notificaciones
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    NotificacionViewSet, CanalNotificacionViewSet, PlantillaNotificacionViewSet
)

app_name = 'notifications'

router = DefaultRouter()
router.register(r'notificaciones', NotificacionViewSet, basename='notificacion')
router.register(r'canal', CanalNotificacionViewSet, basename='canal')
router.register(r'plantillas', PlantillaNotificacionViewSet, basename='plantilla')

urlpatterns = [
    path('', include(router.urls)),
]