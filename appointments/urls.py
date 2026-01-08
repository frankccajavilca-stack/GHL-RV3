from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CitaViewSet, list_ghl_calendars
from .metrics_views import (
    get_system_metrics, 
    get_ghl_metrics, 
    get_webhook_metrics, 
    get_system_health
)

router = DefaultRouter()
router.register(r'citas', CitaViewSet, basename='cita')

urlpatterns = [
    path('', include(router.urls)),
    path('calendars/', list_ghl_calendars, name='ghl-calendars'),
    
    # Endpoints de métricas
    path('metrics/', get_system_metrics, name='system-metrics'),
    path('metrics/ghl/', get_ghl_metrics, name='ghl-metrics'),
    path('metrics/webhooks/', get_webhook_metrics, name='webhook-metrics'),
    path('health/', get_system_health, name='system-health'),
]
