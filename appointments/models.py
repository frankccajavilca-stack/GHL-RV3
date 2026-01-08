from django.db import models
import uuid
from django.core.exceptions import ValidationError
from django.utils import timezone

class Cita(models.Model):
    """
    Modelo principal para citas sincronizadas con GHL
    """
    
    # === Identificadores ===
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    ghl_appointment_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        help_text="ID de la cita en GoHighLevel"
    )
    
    ghl_calendar_id = models.CharField(
        max_length=255,
        db_index=True,
        help_text="ID del calendario en GHL"
    )
    
    # === Información básica ===
    title = models.CharField(
        max_length=255,
        help_text="Título/motivo de la cita"
    )
    
    contact_id = models.CharField(
        max_length=255,
        db_index=True,
        help_text="ID del contacto/paciente en GHL"
    )
    
    assigned_user_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="ID del terapeuta asignado"
    )
    
    # === Horarios (timezone-aware) ===
    start_time = models.DateTimeField(
        db_index=True,
        help_text="Inicio de la cita (UTC en DB, Lima en UI)"
    )
    
    end_time = models.DateTimeField(
        help_text="Fin de la cita (UTC en DB, Lima en UI)"
    )
    
    # === Estado ===
    STATUS_CHOICES = [
        ('scheduled', 'Programada'),
        ('confirmed', 'Confirmada'),
        ('cancelled', 'Cancelada'),
        ('completed', 'Completada'),
        ('no_show', 'No asistió'),
    ]
    
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='scheduled',
        db_index=True
    )
    
    # === Metadata ===
    notes = models.TextField(
        blank=True,
        help_text="Notas adicionales de la cita"
    )
    
    SOURCE_CHOICES = [
        ('rv3', 'Reflexo V3'),
        ('ghl', 'GoHighLevel'),
    ]
    
    source = models.CharField(
        max_length=50,
        choices=SOURCE_CHOICES,
        default='rv3',
        help_text="Origen de la creación"
    )
    
    # === Campos extras para extensibilidad ===
    extra_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Datos adicionales en formato JSON"
    )
    
    # === Auditoría ===
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'citas'
        verbose_name = 'Cita'
        verbose_name_plural = 'Citas'
        ordering = ['start_time']
        
        indexes = [
            models.Index(fields=['ghl_appointment_id']),
            models.Index(fields=['ghl_calendar_id', 'start_time']),
            models.Index(fields=['status', 'start_time']),
            models.Index(fields=['contact_id']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"
    
    def clean(self):
        """Validaciones a nivel de modelo"""
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                raise ValidationError({
                    'end_time': 'La hora de fin debe ser posterior a la hora de inicio'
                })
            
            # Validar duración mínima (15 min)
            duration = (self.end_time - self.start_time).total_seconds() / 60
            if duration < 15:
                raise ValidationError({
                    'end_time': 'La cita debe tener una duración mínima de 15 minutos'
                })
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def duration_minutes(self):
        """Duración de la cita en minutos"""
        if self.start_time and self.end_time:
            return int((self.end_time - self.start_time).total_seconds() / 60)
        return 0
    
    @property
    def is_past(self):
        """Verifica si la cita ya pasó"""
        return self.start_time < timezone.now()
