# 📋 Tareas Pendientes - Proyecto Integrador RV3 ↔ GHL

## 🎯 Resumen Ejecutivo

Este documento detalla las **tareas críticas pendientes** para completar la sincronización bidireccional RV3 ↔ GHL según los requisitos del proyecto integrador.

**Estado actual**: ~60% completado
**Tiempo estimado restante**: 5-7 días
**Prioridad**: ALTA - Sprint activo

---

## 🚨 **FASE 1: CRÍTICAS (2-3 días) - ALTA PRIORIDAD**

### 1.1 Manejo Robusto de Tokens GHL

**Archivo**: `integrations/ghl_client.py`

**Problema**: No hay refresh automático de tokens ni manejo de rate limits.

**Solución**:
```python
# Agregar al ghl_client.py:

import time
import random
from functools import wraps
from django.core.cache import cache

class TokenManager:
    @staticmethod
    def refresh_token():
        """Refresh del access token usando refresh token"""
        # Implementar llamada a GHL OAuth
        pass
    
    @staticmethod
    def is_token_expired(response):
        """Detecta si el token expiró"""
        return response.status_code in [401, 403]

def with_token_refresh_and_backoff(max_retries=3):
    """Decorator para manejo automático de tokens y backoff"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    response = func(*args, **kwargs)
                    
                    # Log rate limit headers
                    if hasattr(response, 'headers'):
                        remaining = response.headers.get('X-RateLimit-Remaining')
                        if remaining:
                            logger.info(f"Rate limit remaining: {remaining}")
                    
                    return response
                    
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 429:
                        # Rate limit - backoff exponencial
                        delay = (2 ** attempt) + random.uniform(0, 1)
                        logger.warning(f"Rate limited, waiting {delay}s")
                        time.sleep(delay)
                        continue
                    elif e.response.status_code in [401, 403]:
                        # Token expirado - refresh
                        logger.info("Token expired, refreshing...")
                        TokenManager.refresh_token()
                        continue
                    else:
                        raise
            raise Exception(f"Max retries ({max_retries}) exceeded")
        return wrapper
    return decorator

# Aplicar decorator a todos los métodos:
@with_token_refresh_and_backoff()
def create_appointment(self, data):
    # código existente...
```

**Tareas específicas**:
- [ ] Implementar `TokenManager.refresh_token()`
- [ ] Agregar decorator a todos los métodos HTTP
- [ ] Configurar variables de entorno para refresh token
- [ ] Agregar logging de rate limits
- [ ] Testing con tokens expirados

---

### 1.2 Idempotencia Fuerte en Webhooks

**Archivo**: `webhooks/handlers.py`

**Problema**: No hay deduplicación de webhooks duplicados.

**Solución**:
```python
# Crear nuevo modelo en webhooks/models.py:

class WebhookEvent(models.Model):
    webhook_id = models.CharField(max_length=255, unique=True)
    event_type = models.CharField(max_length=100)
    ghl_appointment_id = models.CharField(max_length=255)
    processed_at = models.DateTimeField(auto_now_add=True)
    payload_hash = models.CharField(max_length=64)  # SHA256 del payload
    
    class Meta:
        indexes = [
            models.Index(fields=['webhook_id']),
            models.Index(fields=['ghl_appointment_id', 'event_type']),
        ]

# Modificar handlers.py:
from django.db import transaction
from hashlib import sha256
import json

class WebhookHandler:
    @staticmethod
    def is_duplicate_event(webhook_id, payload):
        """Verifica si el evento ya fue procesado"""
        payload_hash = sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        
        return WebhookEvent.objects.filter(
            webhook_id=webhook_id,
            payload_hash=payload_hash
        ).exists()
    
    @staticmethod
    @transaction.atomic
    def handle_appointment_create(data: dict, webhook_id: str = None):
        # Verificar duplicados
        if webhook_id and WebhookHandler.is_duplicate_event(webhook_id, data):
            logger.info(f"Webhook {webhook_id} ya procesado, ignorando")
            return
        
        ghl_appointment_id = data.get('id')
        
        # Select for update para evitar race conditions
        existing = Cita.objects.select_for_update().filter(
            ghl_appointment_id=ghl_appointment_id
        ).first()
        
        if existing:
            logger.info(f"Cita {ghl_appointment_id} ya existe")
            return existing
        
        # Crear cita...
        cita = Cita.objects.create(...)
        
        # Registrar evento procesado
        if webhook_id:
            WebhookEvent.objects.create(
                webhook_id=webhook_id,
                event_type='AppointmentCreate',
                ghl_appointment_id=ghl_appointment_id,
                payload_hash=sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
            )
        
        return cita
```

**Tareas específicas**:
- [ ] Crear modelo `WebhookEvent`
- [ ] Migración de base de datos
- [ ] Modificar todos los handlers con idempotencia
- [ ] Agregar `webhook_id` al endpoint de webhook
- [ ] Testing con webhooks duplicados

---

### 1.3 Endpoint de Discovery de Calendarios

**Archivo**: `appointments/views.py`

**Problema**: No existe endpoint para listar calendarios disponibles.

**Solución**:
```python
# Agregar a appointments/views.py:

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_ghl_calendars(request):
    """
    Lista calendarios disponibles en GHL para la location actual
    """
    try:
        location_id = request.query_params.get('location_id', settings.GHL_LOCATION_ID)
        
        calendars = ghl_client.get_calendars(location_id)
        
        # Formatear respuesta
        formatted_calendars = []
        for cal in calendars.get('calendars', []):
            formatted_calendars.append({
                'id': cal.get('id'),
                'name': cal.get('name'),
                'description': cal.get('description', ''),
                'timezone': cal.get('timezone', 'America/Lima'),
                'isActive': cal.get('isActive', True),
            })
        
        return Response({
            'calendars': formatted_calendars,
            'location_id': location_id,
            'total': len(formatted_calendars)
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo calendarios: {str(e)}")
        return Response(
            {'error': 'Error obteniendo calendarios de GHL'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# Agregar método al ghl_client.py:
def get_calendars(self, location_id):
    """Obtiene calendarios de una location"""
    url = f"{self.base_url}/calendars/"
    params = {'locationId': location_id}
    
    with httpx.Client() as client:
        response = client.get(url, params=params, headers=self._get_headers())
        response.raise_for_status()
        return response.json()
```

**Tareas específicas**:
- [ ] Implementar `get_calendars()` en ghl_client
- [ ] Agregar endpoint en views
- [ ] Actualizar URLs
- [ ] Testing del endpoint
- [ ] Documentar en Postman

---

## 🔧 **FASE 2: ROBUSTEZ (2 días) - MEDIA PRIORIDAD**

### 2.1 Integración Completa de LocationSettings

**Archivos**: `locations/serializers.py`, `locations/views.py`

**Problema**: LocationSettings existe pero no está integrado.

**Solución**:
```python
# Crear locations/serializers.py:
from rest_framework import serializers
from .models import LocationSettings

class LocationSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocationSettings
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

# Crear locations/views.py:
from rest_framework import viewsets
from rest_framework.decorators import action
from .models import LocationSettings
from .serializers import LocationSettingsSerializer

class LocationSettingsViewSet(viewsets.ModelViewSet):
    queryset = LocationSettings.objects.all()
    serializer_class = LocationSettingsSerializer
    
    @action(detail=True, methods=['post'])
    def set_default_calendar(self, request, pk=None):
        """Establece calendario por defecto para una location"""
        location = self.get_object()
        calendar_id = request.data.get('calendar_id')
        
        if not calendar_id:
            return Response({'error': 'calendar_id requerido'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        location.default_calendar_id = calendar_id
        location.save()
        
        return Response({'message': 'Calendario actualizado'})

# Crear locations/urls.py:
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LocationSettingsViewSet

router = DefaultRouter()
router.register(r'settings', LocationSettingsViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
```

**Tareas específicas**:
- [ ] Crear serializers para LocationSettings
- [ ] Implementar ViewSet completo
- [ ] Crear URLs
- [ ] Integrar con selección de calendario en frontend
- [ ] Testing CRUD completo

---

### 2.2 Validaciones de Overlaps y Conflictos

**Archivo**: `appointments/services.py`

**Problema**: No hay validación de solapes de horarios.

**Solución**:
```python
# Agregar a appointments/services.py:

class AppointmentValidationService:
    @staticmethod
    def check_overlaps(start_time, end_time, calendar_id, exclude_id=None):
        """
        Verifica si hay overlaps con otras citas
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
    def validate_business_hours(start_time, end_time):
        """Valida horarios de trabajo (8 AM - 8 PM)"""
        lima_start = to_lima_time(start_time)
        lima_end = to_lima_time(end_time)
        
        if lima_start.hour < 8 or lima_end.hour > 20:
            raise ValidationError("Horario fuera del horario de trabajo (8 AM - 8 PM)")
    
    @staticmethod
    def validate_appointment_data(data, instance=None):
        """Validación completa de datos de cita"""
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        calendar_id = data.get('ghl_calendar_id')
        
        # Validar horarios de trabajo
        AppointmentValidationService.validate_business_hours(start_time, end_time)
        
        # Validar overlaps
        exclude_id = instance.id if instance else None
        has_overlap, overlapping = AppointmentValidationService.check_overlaps(
            start_time, end_time, calendar_id, exclude_id
        )
        
        if has_overlap:
            overlap_details = [
                f"{cita.title} ({cita.start_time} - {cita.end_time})"
                for cita in overlapping[:3]
            ]
            raise ValidationError(
                f"Conflicto de horario con: {', '.join(overlap_details)}"
            )

# Integrar en serializers.py:
def validate(self, data):
    AppointmentValidationService.validate_appointment_data(data, self.instance)
    return super().validate(data)
```

**Tareas específicas**:
- [ ] Implementar validaciones de overlap
- [ ] Agregar validación de horarios de trabajo
- [ ] Integrar en serializers
- [ ] Testing con casos de conflicto
- [ ] Configurar horarios por location

---

### 2.3 Logging Estructurado y Métricas

**Archivo**: `utils/logging_utils.py` (nuevo)

**Problema**: Logging básico, sin métricas ni contexto.

**Solución**:
```python
# Crear utils/logging_utils.py:
import logging
import json
from django.core.cache import cache
from datetime import datetime, timedelta

class StructuredLogger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)
    
    def log_ghl_operation(self, operation, success, details=None, duration=None):
        """Log estructurado para operaciones GHL"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'operation': operation,
            'success': success,
            'duration_ms': duration,
            'details': details or {}
        }
        
        if success:
            self.logger.info(f"GHL_OPERATION: {json.dumps(log_data)}")
        else:
            self.logger.error(f"GHL_OPERATION_FAILED: {json.dumps(log_data)}")
        
        # Actualizar métricas en cache
        self._update_metrics(operation, success)
    
    def _update_metrics(self, operation, success):
        """Actualiza contadores de métricas"""
        key_success = f"ghl_metrics:{operation}:success"
        key_failed = f"ghl_metrics:{operation}:failed"
        
        if success:
            cache.set(key_success, cache.get(key_success, 0) + 1, timeout=3600)
        else:
            cache.set(key_failed, cache.get(key_failed, 0) + 1, timeout=3600)

# Integrar en ghl_client.py:
from utils.logging_utils import StructuredLogger

class GHLClient:
    def __init__(self):
        # ... código existente ...
        self.logger = StructuredLogger('integrations.ghl')
    
    def create_appointment(self, data):
        start_time = time.time()
        try:
            # ... código existente ...
            duration = (time.time() - start_time) * 1000
            self.logger.log_ghl_operation('create_appointment', True, 
                                        {'appointment_id': response.get('id')}, duration)
            return response
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.logger.log_ghl_operation('create_appointment', False, 
                                        {'error': str(e)}, duration)
            raise
```

**Tareas específicas**:
- [ ] Crear utilidad de logging estructurado
- [ ] Integrar en todas las operaciones GHL
- [ ] Configurar métricas en Redis/Cache
- [ ] Crear endpoint para ver métricas
- [ ] Dashboard básico de monitoreo

---

## 📚 **FASE 3: TESTING Y DOCUMENTACIÓN (1-2 días) - BAJA PRIORIDAD**

### 3.1 Colección Postman Completa

**Archivo**: `docs/Reflexo_GHL_Integration.postman_collection.json`

**Contenido requerido**:
```json
{
  "info": {
    "name": "Reflexo GHL Integration",
    "description": "Colección completa para testing de sincronización RV3 ↔ GHL"
  },
  "item": [
    {
      "name": "Citas - CRUD",
      "item": [
        {"name": "Crear Cita", "request": {...}},
        {"name": "Listar Citas", "request": {...}},
        {"name": "Actualizar Cita", "request": {...}},
        {"name": "Cancelar Cita", "request": {...}}
      ]
    },
    {
      "name": "Calendarios",
      "item": [
        {"name": "Listar Calendarios", "request": {...}},
        {"name": "Configurar Calendar por Location", "request": {...}}
      ]
    },
    {
      "name": "Webhooks - Simulación",
      "item": [
        {"name": "Webhook - Appointment Created", "request": {...}},
        {"name": "Webhook - Appointment Updated", "request": {...}},
        {"name": "Webhook - Appointment Deleted", "request": {...}}
      ]
    }
  ]
}
```

**Tareas específicas**:
- [ ] Crear colección base
- [ ] Agregar todos los endpoints
- [ ] Configurar variables de entorno
- [ ] Casos de prueba para cada escenario
- [ ] Exportar y documentar

---

### 3.2 Tests de Integración

**Archivo**: `appointments/tests/test_integration.py`

**Contenido**:
```python
from django.test import TestCase
from unittest.mock import patch, MagicMock
from appointments.models import Cita
from appointments.services import AppointmentSyncService

class GHLIntegrationTestCase(TestCase):
    def setUp(self):
        self.cita_data = {
            'title': 'Test Cita',
            'contact_id': 'test_contact_123',
            'ghl_calendar_id': 'test_calendar_123',
            'start_time': '2025-11-15T14:00:00Z',
            'end_time': '2025-11-15T15:00:00Z',
        }
    
    @patch('integrations.ghl_client.ghl_client.create_appointment')
    def test_create_and_sync_to_ghl(self, mock_create):
        """Test E2E: crear en RV3 y sincronizar a GHL"""
        mock_create.return_value = {'id': 'ghl_123'}
        
        cita = Cita.objects.create(**self.cita_data)
        AppointmentSyncService.sync_to_ghl(cita)
        
        self.assertIsNotNone(cita.ghl_appointment_id)
        mock_create.assert_called_once()
    
    def test_webhook_idempotency(self):
        """Test que webhooks duplicados no creen citas duplicadas"""
        webhook_data = {
            'id': 'ghl_webhook_123',
            'calendarId': 'cal_123',
            'title': 'Webhook Test',
            'contactId': 'contact_123',
            'startTime': '2025-11-15T14:00:00Z',
            'endTime': '2025-11-15T15:00:00Z',
        }
        
        # Procesar webhook dos veces
        WebhookHandler.handle_appointment_create(webhook_data, 'webhook_1')
        WebhookHandler.handle_appointment_create(webhook_data, 'webhook_1')
        
        # Solo debe existir una cita
        self.assertEqual(Cita.objects.count(), 1)
```

**Tareas específicas**:
- [ ] Tests unitarios para cada servicio
- [ ] Tests de integración E2E
- [ ] Tests de idempotencia
- [ ] Tests de validaciones
- [ ] Coverage mínimo 80%

---

### 3.3 Documentación Operativa

**Archivo**: `README_OPERATIVO.md`

**Contenido**:
```markdown
# 🚀 Reflexo V3 - Integración GHL - Guía Operativa

## Instalación y Configuración

### Variables de Entorno Requeridas
```bash
# GHL Configuration
GHL_CLIENT_ID=your_client_id
GHL_CLIENT_SECRET=your_client_secret
GHL_ACCESS_TOKEN=your_access_token
GHL_REFRESH_TOKEN=your_refresh_token
GHL_LOCATION_ID=your_location_id
GHL_WEBHOOK_SECRET=your_webhook_secret

# Redis (para idempotencia)
REDIS_URL=redis://localhost:6379/0
```

### Flujos Principales

#### 1. Crear Cita en RV3 → Sincronizar a GHL
```bash
POST /api/ghl/citas/
{
  "title": "Consulta Fisioterapia",
  "contact_id": "ghl_contact_123",
  "ghl_calendar_id": "cal_456",
  "start_time": "2025-11-15T14:00:00-05:00",
  "end_time": "2025-11-15T15:00:00-05:00"
}
```

#### 2. Webhook GHL → Actualizar RV3
```bash
POST /api/webhooks/ghl/
{
  "type": "AppointmentUpdate",
  "data": {
    "id": "ghl_appointment_789",
    "startTime": "2025-11-15T15:00:00Z"
  }
}
```

### Monitoreo y Troubleshooting

#### Logs Importantes
- `appointments.sync`: Operaciones de sincronización
- `webhooks.processing`: Procesamiento de webhooks
- `integrations.ghl`: Comunicación con GHL API

#### Métricas Clave
- Rate limit remaining: `X-RateLimit-Remaining`
- Operaciones exitosas vs fallidas
- Tiempo de respuesta promedio

### Códigos de Error Comunes
- `401/403`: Token expirado → Se refresca automáticamente
- `429`: Rate limit → Backoff automático
- `5xx`: Error de GHL → Reintentos con backoff
```

**Tareas específicas**:
- [ ] Documentar instalación completa
- [ ] Guía de troubleshooting
- [ ] Ejemplos de uso
- [ ] Códigos de error y soluciones
- [ ] Guía de monitoreo

---

## 🎯 **CRONOGRAMA SUGERIDO**

### **Día 1-2: Críticas**
- ✅ Manejo de tokens y rate limiting
- ✅ Idempotencia de webhooks
- ✅ Endpoint de calendarios

### **Día 3-4: Robustez**
- ✅ LocationSettings completo
- ✅ Validaciones de overlaps
- ✅ Logging estructurado

### **Día 5-6: Testing**
- ✅ Colección Postman
- ✅ Tests de integración
- ✅ Documentación

### **Día 7: Demo y Cierre**
- ✅ Video demo E2E
- ✅ Checklist de aceptación
- ✅ Deploy y validación final

---

## 🚨 **RIESGOS Y MITIGACIONES**

### **Riesgo Alto**: Rate Limits de GHL
**Mitigación**: Implementar backoff exponencial y monitoreo de headers

### **Riesgo Medio**: Webhooks duplicados
**Mitigación**: Idempotencia fuerte con Redis/DB

### **Riesgo Bajo**: Timezone inconsistencies
**Mitigación**: Utilidades centralizadas ya implementadas

---

## ✅ **CHECKLIST DE ACEPTACIÓN**

- [ ] RV3 → GHL: crear/editar/cancelar se refleja correctamente
- [ ] GHL → RV3: webhooks actualizan citas por ghl_appointment_id
- [ ] TZ: todas las fechas en America/Lima sin desfaces
- [ ] Rate limits: manejo automático sin errores visibles
- [ ] Idempotencia: webhooks duplicados no causan problemas
- [ ] CalendarId: seleccionable y persistente por location
- [ ] Docs: README + Postman + video demo listos
- [ ] Tests: cobertura mínima 80% en funciones críticas

---

**Última actualización**: 22 de diciembre de 2025
**Responsable**: Equipo de desarrollo RV3
**Sprint**: 11-17 noviembre 2025