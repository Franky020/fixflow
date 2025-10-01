from rest_framework.routers import DefaultRouter
from .views import SparePartViewSet

router = DefaultRouter()
router.register(r'spareparts', SparePartViewSet, basename='sparepart')

urlpatterns = router.urls