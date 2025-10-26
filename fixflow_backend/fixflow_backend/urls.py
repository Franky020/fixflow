from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from spare_parts.views import SparePartViewSet
from users.views import UserViewSet, LoginView, LogoutView
from tickets.views import TicketViewSet
from reports.views import ReportViewSet
from companies.views import CompanyViewSet
from locations.views import LocationViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'tickets', TicketViewSet)
router.register(r'reports', ReportViewSet)
router.register(r'companies', CompanyViewSet)
router.register(r'locations', LocationViewSet)
router.register(r'spare_parts', SparePartViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/login/', LoginView.as_view(), name='token_obtain_pair'),
    path('api/', include(router.urls)),
    path('api/logout/', LogoutView.as_view(), name='logout'),
]
