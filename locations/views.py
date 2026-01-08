from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from .models import LocationSettings
from .serializers import (
    LocationSettingsSerializer, 
    LocationSettingsCreateSerializer,
    CalendarSelectionSerializer
)
from integrations.ghl_client import ghl_client
import logging

logger = logging.getLogger(__name__)

class LocationSettingsViewSet(viewsets.ModelViewSet):
    """
    ViewSet para CRUD de configuraciones de ubicación/subcuenta GHL
    """
    queryset = LocationSettings.objects.all()
    serializer_class = LocationSettingsSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'timezone']
    search_fields = ['name', 'ghl_location_id']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return LocationSettingsCreateSerializer
        return LocationSettingsSerializer
    
    def get_queryset(self):
        """Filtros adicionales"""
        queryset = super().get_queryset()
        
        # Filtrar solo activas si se especifica
        only_active = self.request.query_params.get('only_active')
        if only_active and only_active.lower() == 'true':
            queryset = queryset.filter(is_active=True)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def set_default_calendar(self, request, pk=None):
        """
        Establece calendario por defecto para una location
        
        Body:
        {
            "calendar_id": "cal_123456"
        }
        """
        location = self.get_object()
        serializer = CalendarSelectionSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        calendar_id = serializer.validated_data['calendar_id']
        
        try:
            # Verificar que el calendario existe en GHL
            calendars_response = ghl_client.get_calendars(location.ghl_location_id)
            calendar_ids = [
                cal.get('id') for cal in calendars_response.get('calendars', [])
            ]
            
            if calendar_id not in calendar_ids:
                return Response(
                    {
                        'error': f'Calendar {calendar_id} no existe en location {location.ghl_location_id}',
                        'available_calendars': calendar_ids
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Actualizar calendario por defecto
            location.default_calendar_id = calendar_id
            location.save(update_fields=['default_calendar_id', 'updated_at'])
            
            logger.info(f"Default calendar updated for location {location.id}: {calendar_id}")
            
            return Response({
                'message': 'Calendario por defecto actualizado exitosamente',
                'location_id': str(location.id),
                'calendar_id': calendar_id,
                'success': True
            })
            
        except Exception as e:
            error_msg = f"Error actualizando calendario por defecto: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return Response(
                {
                    'error': 'Error comunicándose con GHL',
                    'details': str(e),
                    'success': False
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def calendars(self, request, pk=None):
        """
        Lista calendarios disponibles para esta location específica
        """
        location = self.get_object()
        
        try:
            calendars_response = ghl_client.get_calendars(location.ghl_location_id)
            calendars = calendars_response.get('calendars', [])
            
            # Formatear calendarios con información adicional
            formatted_calendars = []
            for cal in calendars:
                formatted_calendars.append({
                    'id': cal.get('id'),
                    'name': cal.get('name'),
                    'description': cal.get('description', ''),
                    'timezone': cal.get('timezone', location.timezone),
                    'isActive': cal.get('isActive', True),
                    'isDefault': cal.get('id') == location.default_calendar_id,
                    'locationId': location.ghl_location_id,
                    'slug': cal.get('slug', ''),
                })
            
            return Response({
                'calendars': formatted_calendars,
                'location': {
                    'id': str(location.id),
                    'name': location.name,
                    'ghl_location_id': location.ghl_location_id,
                    'default_calendar_id': location.default_calendar_id
                },
                'total': len(formatted_calendars),
                'success': True
            })
            
        except Exception as e:
            error_msg = f"Error obteniendo calendarios para location {location.ghl_location_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return Response(
                {
                    'error': 'Error obteniendo calendarios de GHL',
                    'details': str(e),
                    'success': False
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def sync_calendars(self, request, pk=None):
        """
        Sincroniza y actualiza información de calendarios desde GHL
        """
        location = self.get_object()
        
        try:
            calendars_response = ghl_client.get_calendars(location.ghl_location_id)
            calendars = calendars_response.get('calendars', [])
            
            # Verificar si el calendario por defecto aún existe
            calendar_ids = [cal.get('id') for cal in calendars]
            
            if location.default_calendar_id and location.default_calendar_id not in calendar_ids:
                logger.warning(f"Default calendar {location.default_calendar_id} no longer exists for location {location.id}")
                location.default_calendar_id = ''
                location.save(update_fields=['default_calendar_id', 'updated_at'])
            
            return Response({
                'message': 'Calendarios sincronizados exitosamente',
                'calendars_found': len(calendars),
                'calendar_ids': calendar_ids,
                'default_calendar_reset': location.default_calendar_id == '',
                'success': True
            })
            
        except Exception as e:
            error_msg = f"Error sincronizando calendarios: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return Response(
                {
                    'error': 'Error sincronizando con GHL',
                    'details': str(e),
                    'success': False
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def active_locations(self, request):
        """
        Retorna solo las locations activas con sus calendarios por defecto
        """
        active_locations = self.get_queryset().filter(is_active=True)
        
        response_data = []
        for location in active_locations:
            location_data = {
                'id': str(location.id),
                'name': location.name,
                'ghl_location_id': location.ghl_location_id,
                'timezone': location.timezone,
                'default_calendar_id': location.default_calendar_id,
                'has_default_calendar': bool(location.default_calendar_id),
            }
            
            # Intentar obtener nombre del calendario por defecto
            if location.default_calendar_id:
                try:
                    calendars_response = ghl_client.get_calendars(location.ghl_location_id)
                    for cal in calendars_response.get('calendars', []):
                        if cal.get('id') == location.default_calendar_id:
                            location_data['default_calendar_name'] = cal.get('name')
                            break
                except Exception as e:
                    logger.warning(f"Could not fetch calendar name for location {location.id}: {e}")
            
            response_data.append(location_data)
        
        return Response({
            'locations': response_data,
            'total': len(response_data),
            'success': True
        })