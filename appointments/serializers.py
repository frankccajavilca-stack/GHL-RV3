from rest_framework import serializers
from .models import Cita
from .services import AppointmentValidationService
from utils.timezone_utils import normalize_datetime, to_lima_time

class CitaSerializer(serializers.ModelSerializer):
    """
    Serializer principal para el modelo Cita
    """
    
    # Campos computados
    duration_minutes = serializers.IntegerField(read_only=True)
    is_past = serializers.BooleanField(read_only=True)
    
    # Timezone-aware display
    start_time_lima = serializers.SerializerMethodField()
    end_time_lima = serializers.SerializerMethodField()
    
    # Validación de conflictos
    has_conflicts = serializers.SerializerMethodField()
    
    class Meta:
        model = Cita
        fields = [
            'id', 'ghl_appointment_id', 'ghl_calendar_id',
            'title', 'contact_id', 'assigned_user_id',
            'start_time', 'end_time',
            'start_time_lima', 'end_time_lima',
            'status', 'notes', 'source', 'extra_data',
            'duration_minutes', 'is_past', 'has_conflicts',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'ghl_appointment_id']
    
    def get_start_time_lima(self, obj):
        """Retorna hora de inicio en timezone Lima"""
        return to_lima_time(obj.start_time).isoformat()
    
    def get_end_time_lima(self, obj):
        """Retorna hora de fin en timezone Lima"""
        return to_lima_time(obj.end_time).isoformat()
    
    def get_has_conflicts(self, obj):
        """Verifica si la cita tiene conflictos de horario"""
        try:
            has_overlap, _ = AppointmentValidationService.check_overlaps(
                obj.start_time, obj.end_time, obj.ghl_calendar_id, obj.id
            )
            return has_overlap
        except Exception:
            return False
    
    def validate(self, data):
        """Validaciones cross-field con servicio de validación"""
        start = data.get('start_time')
        end = data.get('end_time')
        
        if start and end:
            if start >= end:
                raise serializers.ValidationError({
                    'end_time': 'La hora de fin debe ser posterior a la hora de inicio'
                })
        
        # Aplicar validaciones del servicio
        try:
            # Validación básica siempre
            AppointmentValidationService.validate_appointment_data(
                data, self.instance, strict_validation=False
            )
            
            # Validación estricta solo si se especifica
            strict = self.context.get('strict_validation', True)
            if strict:
                AppointmentValidationService.validate_appointment_data(
                    data, self.instance, strict_validation=True
                )
                
        except Exception as e:
            raise serializers.ValidationError({
                'non_field_errors': [str(e)]
            })
        
        return data
    
    def create(self, validated_data):
        """Override create para normalizar timezone"""
        validated_data['start_time'] = normalize_datetime(validated_data['start_time'])
        validated_data['end_time'] = normalize_datetime(validated_data['end_time'])
        return super().create(validated_data)


class CitaCreateSerializer(CitaSerializer):
    """Serializer específico para creación (campos requeridos)"""
    
    class Meta(CitaSerializer.Meta):
        fields = CitaSerializer.Meta.fields
        extra_kwargs = {
            'title': {'required': True},
            'contact_id': {'required': True},
            'start_time': {'required': True},
            'end_time': {'required': True},
            'ghl_calendar_id': {'required': True},
        }


class CitaQuickCreateSerializer(serializers.ModelSerializer):
    """Serializer para creación rápida sin validaciones estrictas"""
    
    class Meta:
        model = Cita
        fields = [
            'title', 'contact_id', 'ghl_calendar_id',
            'start_time', 'end_time', 'notes', 'assigned_user_id'
        ]
        extra_kwargs = {
            'title': {'required': True},
            'contact_id': {'required': True},
            'start_time': {'required': True},
            'end_time': {'required': True},
            'ghl_calendar_id': {'required': True},
        }
    
    def validate(self, data):
        """Validaciones mínimas para creación rápida"""
        start = data.get('start_time')
        end = data.get('end_time')
        
        if start and end and start >= end:
            raise serializers.ValidationError({
                'end_time': 'La hora de fin debe ser posterior a la hora de inicio'
            })
        
        # Solo validaciones básicas, sin overlaps ni horarios de trabajo
        try:
            AppointmentValidationService.validate_duration(start, end)
        except Exception as e:
            raise serializers.ValidationError({'non_field_errors': [str(e)]})
        
        return data
