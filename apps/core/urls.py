from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    CustomTokenObtainPairView, UserViewSet, EnteRectorViewSet,
    HidrologicaViewSet, AcueductoViewSet
)

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'ente-rector', EnteRectorViewSet)
router.register(r'hidrologicas', HidrologicaViewSet)
router.register(r'acueductos', AcueductoViewSet)

urlpatterns = [
    # Autenticación JWT
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # API endpoints
    path('', include(router.urls)),
]