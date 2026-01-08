from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.conf import settings
from .models import Cita
from .serializers import CitaSerializer, CitaCreateSerializer
from .services import AppointmentSyncService
from integrations.ghl_client import ghl_client
import logging

logger = logging.getLogger(__name__)

class CitaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para CRUD de citas con sincronización a GHL
    """
    queryset = Cita.objects.all()
    serializer_class = CitaSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['status', 'ghl_calendar_id', 'source']
    ordering_fields = ['start_time', 'created_at']
    search_fields = ['title', 'notes', 'contact_id']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CitaCreateSerializer
        return CitaSerializer
    
    def get_queryset(self):
        """Filtros adicionales por query params"""
        queryset = super().get_queryset()
        
        # Filtro por rango de fechas
        desde = self.request.query_params.get('desde')
        hasta = self.request.query_params.get('hasta')
        
        if desde:
            queryset = queryset.filter(start_time__gte=desde)
        if hasta:
            queryset = queryset.filter(start_time__lte=hasta)
        
        # Filtro por calendario
        calendar_id = self.request.query_params.get('calendar_id')
        if calendar_id:
            queryset = queryset.filter(ghl_calendar_id=calendar_id)
        
        return queryset.order_by('start_time')
    
    def perform_create(self, serializer):
        """Override para sincronizar con GHL después de crear"""
        cita = serializer.save()
        
        try:
            # Sincronizar con GHL
            AppointmentSyncService.sync_to_ghl(cita)
            logger.info(f"Cita {cita.id} creada y sincronizada con GHL")
        except Exception as e:
            logger.error(f"Error sincronizando cita {cita.id} a GHL: {e}")
            # No fallar la creación, solo loggear
    
    def perform_update(self, serializer):
        """Override para sincronizar actualizaciones con GHL"""
        cita = serializer.save()
        
        if cita.ghl_appointment_id:
            try:
                AppointmentSyncService.sync_to_ghl(cita)
                logger.info(f"Cita {cita.id} actualizada y sincronizada con GHL")
            except Exception as e:
                logger.error(f"Error sincronizando actualización a GHL: {e}")
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Endpoint para cancelar cita"""
        cita = self.get_object()
        
        if cita.status == 'cancelled':
            return Response(
                {'error': 'La cita ya está cancelada'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        cita.status = 'cancelled'
        cita.save()
        
        # Sincronizar cancelación con GHL
        if cita.ghl_appointment_id:
            try:
                AppointmentSyncService.cancel_in_ghl(cita)
            except Exception as e:
                logger.error(f"Error cancelando en GHL: {e}")
        
        serializer = self.get_serializer(cita)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Retorna citas próximas (futuras)"""
        from django.utils import timezone
        
        upcoming = self.get_queryset().filter(
            start_time__gte=timezone.now(),
            status__in=['scheduled', 'confirmed']
        ).order_by('start_time')[:20]
        
        serializer = self.get_serializer(upcoming, many=True)
        return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_ghl_calendars(request):
    """
    Lista calendarios disponibles en GHL para la location actual
    
    Query params:
    - location_id: ID de la location (opcional, usa default si no se especifica)
    """
    try:
        location_id = request.query_params.get('location_id', settings.GHL_LOCATION_ID)
        
        if not location_id:
            return Response(
                {'error': 'No location_id provided and no default configured'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        logger.info(f"Fetching calendars for location: {location_id}")
        calendars_response = ghl_client.get_calendars(location_id)
        
        # Formatear respuesta
        formatted_calendars = []
        calendars_list = calendars_response.get('calendars', [])
        
        for cal in calendars_list:
            formatted_calendars.append({
                'id': cal.get('id'),
                'name': cal.get('name'),
                'description': cal.get('description', ''),
                'timezone': cal.get('timezone', 'America/Lima'),
                'isActive': cal.get('isActive', True),
                'locationId': cal.get('locationId', location_id),
                'slug': cal.get('slug', ''),
            })
        
        response_data = {
            'calendars': formatted_calendars,
            'location_id': location_id,
            'total': len(formatted_calendars),
            'success': True
        }
        
        logger.info(f"Successfully fetched {len(formatted_calendars)} calendars")
        return Response(response_data)
        
    except Exception as e:
        error_msg = f"Error obteniendo calendarios: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return Response(
            {
                'error': 'Error obteniendo calendarios de GHL',
                'details': str(e),
                'success': False
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
