from rest_framework.routers import DefaultRouter
from .views import ReportViewSet, ReportMessageViewSet

router = DefaultRouter()
router.register(r'reports', ReportViewSet, basename='report')
router.register(r'report_messages', ReportMessageViewSet, basename='report-messages')

urlpatterns = router.urls