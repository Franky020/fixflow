from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from spare_parts.views import SparePartViewSet
from users.views import UserViewSet, LoginView, LogoutView,  RegisterDeviceTokenView
from tickets.views import TicketViewSet
from reports.views import ReportViewSet, ReportMessageViewSet
from companies.views import CompanyViewSet
from locations.views import LocationViewSet
from satisfaction.views import CustomerSatisfactionViewSet
from django.conf import settings
from django.conf.urls.static import static

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'tickets', TicketViewSet, basename='ticket')
router.register(r'satisfaction', CustomerSatisfactionViewSet, basename='satisfaction') 
router.register(r'reports', ReportViewSet, basename='reports')
router.register(r'companies', CompanyViewSet, basename='company')
router.register(r'locations', LocationViewSet, basename='location')
router.register(r'spare_parts', SparePartViewSet, basename='sparepart')
router.register(r'report_messages', ReportMessageViewSet, basename='reportmessage')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/login/', LoginView.as_view(), name='token_obtain_pair'),
    path('api/', include(router.urls)),
    path('api/logout/', LogoutView.as_view(), name='logout'),
    path('api/register_device_token/', RegisterDeviceTokenView.as_view(), name='register_device_token'),
    path('api/', include('reports.urls')),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
