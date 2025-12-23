from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ItemInventarioViewSet, CategoriaItemViewSet

router = DefaultRouter()
router.register(r'items', ItemInventarioViewSet)
router.register(r'categorias', CategoriaItemViewSet)

urlpatterns = [
    path('', include(router.urls)),
]