from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LocationSettingsViewSet

router = DefaultRouter()
router.register(r'settings', LocationSettingsViewSet, basename='location-settings')

urlpatterns = [
    path('', include(router.urls)),
]