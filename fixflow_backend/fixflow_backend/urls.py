from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from spare_parts.views import SparePartViewSet
from users.views import UserViewSet, LoginView, LogoutView,  RegisterDeviceTokenView
from tickets.views import TicketViewSet
from reports.views import ReportViewSet, ReportMessageViewSet
from companies.views import CompanyViewSet
from locations.views import LocationViewSet
from django.conf import settings
from django.conf.urls.static import static

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'tickets', TicketViewSet, basename='ticket')
router.register(r'reports', ReportViewSet)
router.register(r'companies', CompanyViewSet)
router.register(r'locations', LocationViewSet)
router.register(r'spare_parts', SparePartViewSet)
router.register(r'report_messages', ReportMessageViewSet)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/login/', LoginView.as_view(), name='token_obtain_pair'),
    path('api/', include(router.urls)),
    path('api/logout/', LogoutView.as_view(), name='logout'),
    path('api/register_device_token/', RegisterDeviceTokenView.as_view(), name='register_device_token'),
    path('api/', include('reports.urls')),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
