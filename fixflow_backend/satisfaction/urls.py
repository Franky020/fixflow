from rest_framework.routers import DefaultRouter
from .views import CustomerSatisfactionViewSet
from django.urls import path, include

router = DefaultRouter()
# Registramos solo las rutas que pertenecen a esta app
router.register(r'', CustomerSatisfactionViewSet, basename='satisfaction')

urlpatterns = [
    # Incluimos todas las rutas generadas por el router en la raíz de esta app
    path('', include(router.urls)),
]