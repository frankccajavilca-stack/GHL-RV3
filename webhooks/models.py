from django.db import models
import uuid

class WebhookEvent(models.Model):
    """
    Registro de eventos de webhook procesados para idempotencia
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    webhook_id = models.CharField(
        max_length=255,
        unique=True,
        help_text="ID único del webhook (puede ser generado o enviado por GHL)"
    )
    
    event_type = models.CharField(
        max_length=100,
        help_text="Tipo de evento: AppointmentCreate, AppointmentUpdate, AppointmentDelete"
    )
    
    ghl_appointment_id = models.CharField(
        max_length=255,
        help_text="ID de la cita en GHL"
    )
    
    processed_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp de cuando se procesó el evento"
    )
    
    payload_hash = models.CharField(
        max_length=64,
        help_text="SHA256 hash del payload para detectar duplicados exactos"
    )
    
    success = models.BooleanField(
        default=True,
        help_text="Si el procesamiento fue exitoso"
    )
    
    error_message = models.TextField(
        blank=True,
        help_text="Mensaje de error si el procesamiento falló"
    )
    
    class Meta:
        db_table = 'webhook_events'
        verbose_name = 'Evento de Webhook'
        verbose_name_plural = 'Eventos de Webhook'
        ordering = ['-processed_at']
        
        indexes = [
            models.Index(fields=['webhook_id']),
            models.Index(fields=['ghl_appointment_id', 'event_type']),
            models.Index(fields=['processed_at']),
            models.Index(fields=['payload_hash']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.ghl_appointment_id} ({self.processed_at})"