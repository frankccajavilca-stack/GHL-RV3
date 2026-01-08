from .models import Cita
from integrations.ghl_client import ghl_client
from django.conf import settings
from django.core.exceptions import ValidationError
from utils.timezone_utils import to_utc_iso, to_lima_time
import logging

logger = logging.getLogger(__name__)

class AppointmentSyncService:
    """
    Servicio para sincronización bidireccional RV3 ↔ GHL
    """
    
    @staticmethod
    def map_to_ghl_format(cita: Cita) -> dict:
        """Convierte Cita a formato GHL API"""
        return {
            "calendarId": cita.ghl_calendar_id,
            "locationId": settings.GHL_LOCATION_ID,
            "contactId": cita.contact_id,
            "startTime": to_utc_iso(cita.start_time),
            "endTime": to_utc_iso(cita.end_time),
            "title": cita.title,
            "appointmentStatus": cita.status,
            "assignedUserId": cita.assigned_user_id,
            "notes": cita.notes,
        }
    
    @classmethod
    def sync_to_ghl(cls, cita: Cita) -> dict:
        """
        Sincroniza cita de RV3 a GHL
        
        Args:
            cita: Instancia de Cita a sincronizar
            
        Returns:
            Response de GHL API
            
        Raises:
            Exception: Si falla la sincronización
        """
        try:
            ghl_data = cls.map_to_ghl_format(cita)
            
            # Crear o actualizar en GHL
            if cita.ghl_appointment_id:
                # Actualizar existente
                response = ghl_client.update_appointment(
                    cita.ghl_appointment_id,
                    ghl_data
                )
                logger.info(f"Cita {cita.id} actualizada en GHL")
            else:
                # Crear nueva
                response = ghl_client.create_appointment(ghl_data)
                
                # Guardar ID de GHL
                cita.ghl_appointment_id = response.get('id')
                cita.save(update_fields=['ghl_appointment_id', 'updated_at'])
                
                logger.info(f"Cita {cita.id} creada en GHL con ID {cita.ghl_appointment_id}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error sincronizando cita {cita.id} a GHL: {str(e)}")
            raise
    
    @classmethod
    def cancel_in_ghl(cls, cita: Cita):
        """Cancela cita en GHL"""
        if not cita.ghl_appointment_id:
            logger.warning(f"Cita {cita.id} no tiene ghl_appointment_id, no se puede cancelar en GHL")
            return
        
        try:
            ghl_client.cancel_appointment(cita.ghl_appointment_id)
            logger.info(f"Cita {cita.id} cancelada en GHL")
        except Exception as e:
            logger.error(f"Error cancelando cita {cita.id} en GHL: {str(e)}")
            raise


class AppointmentValidationService:
    """
    Servicio para validaciones de citas y prevención de conflictos
    """
    
    @staticmethod
    def check_overlaps(start_time, end_time, calendar_id, exclude_id=None):
        """
        Verifica si hay overlaps con otras citas
        
        Args:
            start_time: Datetime de inicio
            end_time: Datetime de fin
            calendar_id: ID del calendario
            exclude_id: ID de cita a excluir (para actualizaciones)
            
        Returns:
            tuple: (has_overlap: bool, overlapping_citas: QuerySet)
        """
        overlapping = Cita.objects.filter(
            ghl_calendar_id=calendar_id,
            status__in=['scheduled', 'confirmed'],
            start_time__lt=end_time,
            end_time__gt=start_time
        )
        
        if exclude_id:
            overlapping = overlapping.exclude(id=exclude_id)
        
        return overlapping.exists(), overlapping
    
    @staticmethod
    def validate_business_hours(start_time, end_time, business_start=8, business_end=20):
        """
        Valida horarios de trabajo
        
        Args:
            start_time: Datetime de inicio
            end_time: Datetime de fin
            business_start: Hora de inicio (default: 8 AM)
            business_end: Hora de fin (default: 8 PM)
        """
        lima_start = to_lima_time(start_time)
        lima_end = to_lima_time(end_time)
        
        if lima_start.hour < business_start or lima_end.hour > business_end:
            raise ValidationError(
                f"Horario fuera del horario de trabajo ({business_start}:00 AM - {business_end}:00 PM)"
            )
        
        # Validar que no sea fin de semana (opcional)
        if lima_start.weekday() >= 5:  # 5=Sábado, 6=Domingo
            logger.warning(f"Cita programada en fin de semana: {lima_start.strftime('%A')}")
    
    @staticmethod
    def validate_duration(start_time, end_time, min_minutes=15, max_minutes=480):
        """
        Valida duración de la cita
        
        Args:
            start_time: Datetime de inicio
            end_time: Datetime de fin
            min_minutes: Duración mínima en minutos (default: 15)
            max_minutes: Duración máxima en minutos (default: 480 = 8 horas)
        """
        duration_seconds = (end_time - start_time).total_seconds()
        duration_minutes = duration_seconds / 60
        
        if duration_minutes < min_minutes:
            raise ValidationError(f"La duración mínima es {min_minutes} minutos")
        
        if duration_minutes > max_minutes:
            raise ValidationError(f"La duración máxima es {max_minutes} minutos ({max_minutes//60} horas)")
    
    @staticmethod
    def validate_future_date(start_time, allow_past=False):
        """
        Valida que la cita sea en el futuro
        
        Args:
            start_time: Datetime de inicio
            allow_past: Si permite citas en el pasado (default: False)
        """
        from django.utils import timezone
        
        if not allow_past and start_time < timezone.now():
            raise ValidationError("No se pueden crear citas en el pasado")
    
    @staticmethod
    def validate_calendar_availability(calendar_id, location_id=None):
        """
        Valida que el calendario esté disponible y activo
        
        Args:
            calendar_id: ID del calendario
            location_id: ID de la location (opcional)
        """
        try:
            calendars_response = ghl_client.get_calendars(location_id or settings.GHL_LOCATION_ID)
            calendars = calendars_response.get('calendars', [])
            
            for cal in calendars:
                if cal.get('id') == calendar_id:
                    if not cal.get('isActive', True):
                        raise ValidationError(f"El calendario {calendar_id} está inactivo")
                    return True
            
            raise ValidationError(f"El calendario {calendar_id} no existe o no está disponible")
            
        except Exception as e:
            logger.error(f"Error validando calendario {calendar_id}: {str(e)}")
            raise ValidationError(f"Error validando calendario: {str(e)}")
    
    @staticmethod
    def validate_appointment_data(data, instance=None, strict_validation=True):
        """
        Validación completa de datos de cita
        
        Args:
            data: Diccionario con datos de la cita
            instance: Instancia existente (para actualizaciones)
            strict_validation: Si aplicar validaciones estrictas
        """
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        calendar_id = data.get('ghl_calendar_id')
        
        if not all([start_time, end_time, calendar_id]):
            raise ValidationError("start_time, end_time y ghl_calendar_id son requeridos")
        
        # Validar duración
        AppointmentValidationService.validate_duration(start_time, end_time)
        
        # Validar fecha futura (solo para nuevas citas)
        if not instance:
            AppointmentValidationService.validate_future_date(start_time)
        
        if strict_validation:
            # Validar horarios de trabajo
            AppointmentValidationService.validate_business_hours(start_time, end_time)
            
            # Validar disponibilidad del calendario
            AppointmentValidationService.validate_calendar_availability(calendar_id)
            
            # Validar overlaps
            exclude_id = instance.id if instance else None
            has_overlap, overlapping = AppointmentValidationService.check_overlaps(
                start_time, end_time, calendar_id, exclude_id
            )
            
            if has_overlap:
                overlap_details = []
                for cita in overlapping[:3]:  # Mostrar máximo 3 conflictos
                    lima_start = to_lima_time(cita.start_time)
                    lima_end = to_lima_time(cita.end_time)
                    overlap_details.append(
                        f"{cita.title} ({lima_start.strftime('%H:%M')} - {lima_end.strftime('%H:%M')})"
                    )
                
                raise ValidationError(
                    f"Conflicto de horario con: {', '.join(overlap_details)}"
                )
        
        logger.info(f"Validación de cita exitosa para calendario {calendar_id}")
        return True
