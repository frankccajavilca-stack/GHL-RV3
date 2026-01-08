from rest_framework import serializers
from .models import LocationSettings
from integrations.ghl_client import ghl_client
import logging

logger = logging.getLogger(__name__)

class LocationSettingsSerializer(serializers.ModelSerializer):
    """
    Serializer para configuraciones de ubicación/subcuenta GHL
    """
    
    # Campos computados
    available_calendars = serializers.SerializerMethodField()
    calendar_count = serializers.SerializerMethodField()
    
    class Meta:
        model = LocationSettings
        fields = [
            'id', 'ghl_location_id', 'name', 'timezone',
            'default_calendar_id', 'is_active',
            'available_calendars', 'calendar_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_available_calendars(self, obj):
        """Obtiene calendarios disponibles para esta location"""
        try:
            if obj.ghl_location_id:
                calendars_response = ghl_client.get_calendars(obj.ghl_location_id)
                calendars = calendars_response.get('calendars', [])
                
                return [
                    {
                        'id': cal.get('id'),
                        'name': cal.get('name'),
                        'isActive': cal.get('isActive', True),
                        'isDefault': cal.get('id') == obj.default_calendar_id
                    }
                    for cal in calendars
                ]
        except Exception as e:
            logger.warning(f"Error fetching calendars for location {obj.ghl_location_id}: {e}")
        
        return []
    
    def get_calendar_count(self, obj):
        """Cuenta calendarios disponibles"""
        calendars = self.get_available_calendars(obj)
        return len(calendars)
    
    def validate_ghl_location_id(self, value):
        """Valida que el location_id sea válido en GHL"""
        if not value:
            raise serializers.ValidationError("Location ID es requerido")
        
        try:
            # Intentar obtener calendarios para validar el location_id
            ghl_client.get_calendars(value)
            return value
        except Exception as e:
            raise serializers.ValidationError(
                f"Location ID inválido o no accesible: {str(e)}"
            )
    
    def validate_default_calendar_id(self, value):
        """Valida que el calendar_id exista en la location"""
        if not value:
            return value
        
        # Obtener location_id del contexto
        ghl_location_id = None
        if self.instance:
            ghl_location_id = self.instance.ghl_location_id
        elif 'ghl_location_id' in self.initial_data:
            ghl_location_id = self.initial_data['ghl_location_id']
        
        if ghl_location_id:
            try:
                calendars_response = ghl_client.get_calendars(ghl_location_id)
                calendar_ids = [
                    cal.get('id') for cal in calendars_response.get('calendars', [])
                ]
                
                if value not in calendar_ids:
                    raise serializers.ValidationError(
                        f"Calendar ID {value} no existe en la location {ghl_location_id}"
                    )
            except Exception as e:
                logger.warning(f"Could not validate calendar_id: {e}")
        
        return value


class LocationSettingsCreateSerializer(LocationSettingsSerializer):
    """Serializer específico para creación con validaciones estrictas"""
    
    class Meta(LocationSettingsSerializer.Meta):
        fields = LocationSettingsSerializer.Meta.fields
        extra_kwargs = {
            'ghl_location_id': {'required': True},
            'name': {'required': True},
        }


class CalendarSelectionSerializer(serializers.Serializer):
    """Serializer para seleccionar calendario por defecto"""
    
    calendar_id = serializers.CharField(
        max_length=255,
        required=True,
        help_text="ID del calendario a establecer como predeterminado"
    )
    
    def validate_calendar_id(self, value):
        """Valida que el calendar_id sea válido"""
        if not value:
            raise serializers.ValidationError("Calendar ID es requerido")
        return value