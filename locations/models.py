from django.db import models
import uuid


class LocationSettings(models.Model):
    """
    Configuración de ubicación/subcuenta de GHL
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    ghl_location_id = models.CharField(
        max_length=255,
        unique=True,
        help_text="ID de la ubicación/subcuenta en GHL"
    )
    
    name = models.CharField(
        max_length=255,
        help_text="Nombre de la ubicación"
    )
    
    timezone = models.CharField(
        max_length=100,
        default='America/Lima',
        help_text="Timezone de la ubicación"
    )
    
    default_calendar_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="ID del calendario por defecto"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Si la sincronización está activa"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'location_settings'
        verbose_name = 'Configuración de Ubicación'
        verbose_name_plural = 'Configuraciones de Ubicación'
    
    def __str__(self):
        return f"{self.name} ({self.ghl_location_id})"
