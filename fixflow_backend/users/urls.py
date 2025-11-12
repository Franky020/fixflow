from rest_framework.routers import DefaultRouter
from .views import UserViewSet
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import Login 

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'login', TokenObtainPairView.as_view(serializer_class=Login), basename='login')



urlpatterns = router.urls