from django.db import transaction
from hashlib import sha256
import json
import uuid
from appointments.models import Cita
from .models import WebhookEvent
from utils.timezone_utils import normalize_datetime
from utils.logging_utils import StructuredLogger
import logging

logger = logging.getLogger(__name__)


class WebhookHandler:
    """
    Handlers para eventos de webhook de GHL con idempotencia fuerte
    """
    
    def __init__(self):
        self.structured_logger = StructuredLogger('webhooks.processing')
    
    @staticmethod
    def generate_webhook_id(data: dict) -> str:
        """Genera un ID único para el webhook basado en el contenido"""
        content = json.dumps(data, sort_keys=True)
        return sha256(content.encode()).hexdigest()[:16]
    
    @staticmethod
    def is_duplicate_event(webhook_id: str, payload: dict) -> bool:
        """Verifica si el evento ya fue procesado"""
        payload_hash = sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        
        return WebhookEvent.objects.filter(
            webhook_id=webhook_id,
            payload_hash=payload_hash
        ).exists()
    
    @staticmethod
    def record_webhook_event(webhook_id: str, event_type: str, ghl_appointment_id: str, 
                           payload: dict, success: bool = True, error_message: str = ""):
        """Registra el evento procesado"""
        payload_hash = sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        
        WebhookEvent.objects.create(
            webhook_id=webhook_id,
            event_type=event_type,
            ghl_appointment_id=ghl_appointment_id,
            payload_hash=payload_hash,
            success=success,
            error_message=error_message
        )
    
    @staticmethod
    @transaction.atomic
    def handle_appointment_create(data: dict, webhook_id: str = None):
        """
        Procesa evento de creación de cita desde GHL con idempotencia
        """
        structured_logger = StructuredLogger('webhooks.processing')
        
        if not webhook_id:
            webhook_id = WebhookHandler.generate_webhook_id(data)
        
        ghl_appointment_id = data.get('id')
        
        # Log inicio del procesamiento
        structured_logger.log_webhook_event(
            'AppointmentCreate', True, webhook_id, ghl_appointment_id,
            {'status': 'processing_started'}
        )
        
        # Verificar duplicados
        if WebhookHandler.is_duplicate_event(webhook_id, data):
            logger.info(f"Webhook {webhook_id} ya procesado, ignorando")
            structured_logger.log_webhook_event(
                'AppointmentCreate', True, webhook_id, ghl_appointment_id,
                {'status': 'duplicate_ignored'}
            )
            return None
        
        try:
            # Select for update para evitar race conditions
            existing = Cita.objects.select_for_update().filter(
                ghl_appointment_id=ghl_appointment_id
            ).first()
            
            if existing:
                logger.info(f"Cita {ghl_appointment_id} ya existe, actualizando desde webhook")
                # Actualizar datos existentes
                existing.title = data.get('title', existing.title)
                existing.contact_id = data.get('contactId', existing.contact_id)
                existing.assigned_user_id = data.get('assignedUserId', existing.assigned_user_id)
                existing.status = data.get('appointmentStatus', existing.status)
                existing.notes = data.get('notes', existing.notes)
                
                if data.get('startTime'):
                    existing.start_time = normalize_datetime(data.get('startTime'))
                if data.get('endTime'):
                    existing.end_time = normalize_datetime(data.get('endTime'))
                
                existing.save()
                
                # Registrar evento
                WebhookHandler.record_webhook_event(
                    webhook_id, 'AppointmentCreate', ghl_appointment_id, data, True
                )
                
                structured_logger.log_webhook_event(
                    'AppointmentCreate', True, webhook_id, ghl_appointment_id,
                    {'status': 'updated_existing', 'cita_id': str(existing.id)}
                )
                
                return existing
            
            # Crear nueva cita
            cita = Cita.objects.create(
                ghl_appointment_id=ghl_appointment_id,
                ghl_calendar_id=data.get('calendarId', ''),
                title=data.get('title', 'Cita desde GHL'),
                contact_id=data.get('contactId', ''),
                assigned_user_id=data.get('assignedUserId'),
                start_time=normalize_datetime(data.get('startTime')),
                end_time=normalize_datetime(data.get('endTime')),
                status=data.get('appointmentStatus', 'scheduled'),
                notes=data.get('notes', ''),
                source='ghl',
            )
            
            # Registrar evento procesado
            WebhookHandler.record_webhook_event(
                webhook_id, 'AppointmentCreate', ghl_appointment_id, data, True
            )
            
            structured_logger.log_webhook_event(
                'AppointmentCreate', True, webhook_id, ghl_appointment_id,
                {'status': 'created_new', 'cita_id': str(cita.id)}
            )
            
            logger.info(f"Cita creada desde webhook GHL: {cita.id}")
            return cita
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error creando cita desde webhook: {error_msg}")
            
            # Registrar evento fallido
            WebhookHandler.record_webhook_event(
                webhook_id, 'AppointmentCreate', ghl_appointment_id, data, False, error_msg
            )
            
            structured_logger.log_webhook_event(
                'AppointmentCreate', False, webhook_id, ghl_appointment_id,
                {'status': 'error', 'error': error_msg}
            )
            
            raise
    
    @staticmethod
    @transaction.atomic
    def handle_appointment_update(data: dict, webhook_id: str = None):
        """
        Procesa evento de actualización de cita desde GHL con idempotencia
        """
        structured_logger = StructuredLogger('webhooks.processing')
        
        if not webhook_id:
            webhook_id = WebhookHandler.generate_webhook_id(data)
        
        # Verificar duplicados
        if WebhookHandler.is_duplicate_event(webhook_id, data):
            logger.info(f"Webhook {webhook_id} ya procesado, ignorando")
            return None
        
        ghl_appointment_id = data.get('id')
        
        try:
            cita = Cita.objects.select_for_update().filter(
                ghl_appointment_id=ghl_appointment_id
            ).first()
            
            if not cita:
                logger.warning(f"Cita no encontrada para actualizar: {ghl_appointment_id}")
                # Crear la cita si no existe
                return WebhookHandler.handle_appointment_create(data, webhook_id)
            
            # Actualizar campos
            cita.title = data.get('title', cita.title)
            cita.contact_id = data.get('contactId', cita.contact_id)
            cita.assigned_user_id = data.get('assignedUserId', cita.assigned_user_id)
            cita.status = data.get('appointmentStatus', cita.status)
            cita.notes = data.get('notes', cita.notes)
            
            if data.get('startTime'):
                cita.start_time = normalize_datetime(data.get('startTime'))
            if data.get('endTime'):
                cita.end_time = normalize_datetime(data.get('endTime'))
            
            cita.save()
            
            # Registrar evento procesado
            WebhookHandler.record_webhook_event(
                webhook_id, 'AppointmentUpdate', ghl_appointment_id, data, True
            )
            
            structured_logger.log_webhook_event(
                'AppointmentUpdate', True, webhook_id, ghl_appointment_id,
                {'status': 'updated', 'cita_id': str(cita.id)}
            )
            
            logger.info(f"Cita actualizada desde webhook GHL: {cita.id}")
            return cita
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error actualizando cita desde webhook: {error_msg}")
            
            # Registrar evento fallido
            WebhookHandler.record_webhook_event(
                webhook_id, 'AppointmentUpdate', ghl_appointment_id, data, False, error_msg
            )
            
            structured_logger.log_webhook_event(
                'AppointmentUpdate', False, webhook_id, ghl_appointment_id,
                {'status': 'error', 'error': error_msg}
            )
            
            raise
    
    @staticmethod
    @transaction.atomic
    def handle_appointment_delete(data: dict, webhook_id: str = None):
        """
        Procesa evento de eliminación/cancelación de cita desde GHL con idempotencia
        """
        structured_logger = StructuredLogger('webhooks.processing')
        
        if not webhook_id:
            webhook_id = WebhookHandler.generate_webhook_id(data)
        
        # Verificar duplicados
        if WebhookHandler.is_duplicate_event(webhook_id, data):
            logger.info(f"Webhook {webhook_id} ya procesado, ignorando")
            return None
        
        ghl_appointment_id = data.get('id')
        
        try:
            cita = Cita.objects.select_for_update().filter(
                ghl_appointment_id=ghl_appointment_id
            ).first()
            
            if not cita:
                logger.warning(f"Cita no encontrada para cancelar: {ghl_appointment_id}")
                # Registrar evento aunque no exista la cita
                WebhookHandler.record_webhook_event(
                    webhook_id, 'AppointmentDelete', ghl_appointment_id, data, True, 
                    "Cita no encontrada, pero evento registrado"
                )
                
                structured_logger.log_webhook_event(
                    'AppointmentDelete', True, webhook_id, ghl_appointment_id,
                    {'status': 'not_found'}
                )
                
                return None
            
            cita.status = 'cancelled'
            cita.save(update_fields=['status', 'updated_at'])
            
            # Registrar evento procesado
            WebhookHandler.record_webhook_event(
                webhook_id, 'AppointmentDelete', ghl_appointment_id, data, True
            )
            
            structured_logger.log_webhook_event(
                'AppointmentDelete', True, webhook_id, ghl_appointment_id,
                {'status': 'cancelled', 'cita_id': str(cita.id)}
            )
            
            logger.info(f"Cita cancelada desde webhook GHL: {cita.id}")
            return cita
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error cancelando cita desde webhook: {error_msg}")
            
            # Registrar evento fallido
            WebhookHandler.record_webhook_event(
                webhook_id, 'AppointmentDelete', ghl_appointment_id, data, False, error_msg
            )
            
            structured_logger.log_webhook_event(
                'AppointmentDelete', False, webhook_id, ghl_appointment_id,
                {'status': 'error', 'error': error_msg}
            )
            
            raise
