# 🚀 Reflexo V3 - Integración GHL - Guía Operativa Completa

## 📋 Índice

1. [Instalación y Configuración](#instalación-y-configuración)
2. [Variables de Entorno](#variables-de-entorno)
3. [Endpoints Disponibles](#endpoints-disponibles)
4. [Flujos Principales](#flujos-principales)
5. [Monitoreo y Métricas](#monitoreo-y-métricas)
6. [Troubleshooting](#troubleshooting)
7. [Testing](#testing)
8. [Códigos de Error](#códigos-de-error)

---

## 🔧 Instalación y Configuración

### Requisitos Previos

- Python 3.9+
- Django 5.2.5
- MySQL 8.0+
- Redis (para cache y métricas)
- Cuenta activa en GoHighLevel

### Instalación

```bash
# 1. Clonar repositorio
git clone <repository-url>
cd Reflexo-V3-main

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar base de datos
python manage.py makemigrations
python manage.py migrate

# 4. Crear superusuario
python manage.py createsuperuser

# 5. Ejecutar servidor
python manage.py runserver
```

---

## 🔐 Variables de Entorno

### Archivo `.env` Requerido

```bash
# ==================== Frontend ====================
FRONTEND_URL=http://localhost:3000

# ==================== CORS ====================
CORS_ALLOW_ALL_ORIGINS=True
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# ==================== Celery (Redis) ====================
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# ==================== GoHighLevel (GHL) - CRÍTICO ====================
GHL_CLIENT_ID=your_client_id_here
GHL_CLIENT_SECRET=your_client_secret_here
GHL_ACCESS_TOKEN=your_access_token_here
GHL_REFRESH_TOKEN=your_refresh_token_here
GHL_LOCATION_ID=your_location_id_here
GHL_WEBHOOK_SECRET=your_webhook_secret_here
```

### Obtener Credenciales GHL

1. **Acceder a GHL Developer Portal**
   - URL: https://marketplace.gohighlevel.com/
   - Crear aplicación OAuth

2. **Configurar OAuth App**
   - Scopes requeridos: `calendars.readonly`, `calendars.write`, `calendars/events.readonly`, `calendars/events.write`
   - Redirect URI: `http://localhost:8000/api/ghl/oauth/callback/`

3. **Obtener Tokens**
   - Usar flujo OAuth 2.0 para obtener access_token y refresh_token
   - Guardar location_id de la subcuenta objetivo

---

## 🔌 Endpoints Disponibles

### Autenticación

```bash
POST /api/architect/login/
# Body: {"username": "admin", "password": "password"}
# Response: {"access": "jwt_token", "refresh": "refresh_token"}
```

### Citas (CRUD + Sincronización)

```bash
# Listar citas
GET /api/ghl/citas/
# Query params: ?page=1&page_size=10&status=scheduled&desde=2025-12-01&hasta=2025-12-31

# Crear cita (sincroniza automáticamente a GHL)
POST /api/ghl/citas/
# Body:
{
  "title": "Consulta Fisioterapia",
  "contact_id": "ghl_contact_123",
  "ghl_calendar_id": "cal_456",
  "start_time": "2025-12-25T14:00:00-05:00",
  "end_time": "2025-12-25T15:00:00-05:00",
  "notes": "Notas de la cita",
  "assigned_user_id": "user_789"
}

# Obtener detalle de cita
GET /api/ghl/citas/{cita_id}/

# Actualizar cita (sincroniza a GHL)
PUT /api/ghl/citas/{cita_id}/

# Cancelar cita (sincroniza a GHL)
POST /api/ghl/citas/{cita_id}/cancel/

# Citas próximas
GET /api/ghl/citas/upcoming/
```

### Calendarios

```bash
# Listar calendarios disponibles en GHL
GET /api/ghl/calendars/
# Query params: ?location_id=CRlTCqv7ASS9xOpPQ59O

# Response:
{
  "calendars": [
    {
      "id": "cal_123",
      "name": "Fisioterapia",
      "description": "Calendario principal",
      "timezone": "America/Lima",
      "isActive": true,
      "locationId": "CRlTCqv7ASS9xOpPQ59O"
    }
  ],
  "total": 1,
  "success": true
}
```

### Locations (Configuración)

```bash
# CRUD de configuraciones de location
GET /api/locations/settings/
POST /api/locations/settings/
GET /api/locations/settings/{id}/
PUT /api/locations/settings/{id}/
DELETE /api/locations/settings/{id}/

# Establecer calendario por defecto
POST /api/locations/settings/{id}/set_default_calendar/
# Body: {"calendar_id": "cal_123"}

# Calendarios de una location específica
GET /api/locations/settings/{id}/calendars/

# Locations activas
GET /api/locations/settings/active_locations/
```

### Webhooks (Recepción desde GHL)

```bash
# Endpoint para webhooks de GHL (sin autenticación)
POST /api/webhooks/ghl/
# Body:
{
  "type": "AppointmentCreate|AppointmentUpdate|AppointmentDelete",
  "locationId": "CRlTCqv7ASS9xOpPQ59O",
  "webhookId": "webhook_unique_id",
  "data": {
    "id": "ghl_appointment_123",
    "calendarId": "cal_456",
    "contactId": "contact_789",
    "title": "Cita desde GHL",
    "startTime": "2025-12-25T19:00:00.000Z",
    "endTime": "2025-12-25T20:00:00.000Z",
    "appointmentStatus": "scheduled"
  }
}
```

### Métricas y Monitoreo

```bash
# Métricas completas del sistema
GET /api/ghl/metrics/

# Métricas específicas de GHL
GET /api/ghl/metrics/ghl/

# Métricas de webhooks
GET /api/ghl/metrics/webhooks/

# Health check del sistema
GET /api/ghl/health/
```

---

## 🔄 Flujos Principales

### 1. Crear Cita en RV3 → Sincronizar a GHL

```bash
# 1. Obtener calendarios disponibles
curl -X GET "http://localhost:8000/api/ghl/calendars/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 2. Crear cita (se sincroniza automáticamente)
curl -X POST "http://localhost:8000/api/ghl/citas/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Consulta Fisioterapia",
    "contact_id": "ghl_contact_123",
    "ghl_calendar_id": "cal_456",
    "start_time": "2025-12-25T14:00:00-05:00",
    "end_time": "2025-12-25T15:00:00-05:00",
    "notes": "Primera consulta"
  }'

# 3. Verificar sincronización
curl -X GET "http://localhost:8000/api/ghl/citas/{cita_id}/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 2. Webhook GHL → Actualizar RV3

```bash
# GHL envía webhook automáticamente cuando hay cambios
# El sistema procesa automáticamente:
# - AppointmentCreate: Crea nueva cita en RV3
# - AppointmentUpdate: Actualiza cita existente
# - AppointmentDelete: Cancela cita en RV3

# Verificar procesamiento
curl -X GET "http://localhost:8000/api/ghl/metrics/webhooks/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 3. Configurar Location y Calendario por Defecto

```bash
# 1. Crear configuración de location
curl -X POST "http://localhost:8000/api/locations/settings/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ghl_location_id": "CRlTCqv7ASS9xOpPQ59O",
    "name": "Reflexo Peru - Principal",
    "timezone": "America/Lima",
    "is_active": true
  }'

# 2. Establecer calendario por defecto
curl -X POST "http://localhost:8000/api/locations/settings/{location_id}/set_default_calendar/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"calendar_id": "cal_123"}'
```

---

## 📊 Monitoreo y Métricas

### Dashboard de Métricas

El sistema proporciona métricas en tiempo real:

```json
{
  "ghl_operations": {
    "create_appointment": {
      "success_count": 45,
      "failed_count": 2,
      "total_count": 47,
      "success_rate": 95.74,
      "avg_duration_ms": 234.5
    },
    "update_appointment": {
      "success_count": 23,
      "failed_count": 0,
      "total_count": 23,
      "success_rate": 100.0,
      "avg_duration_ms": 189.2
    }
  },
  "webhooks": {
    "AppointmentCreate": {
      "success_count": 15,
      "failed_count": 1,
      "total_count": 16,
      "success_rate": 93.75
    }
  },
  "system_health": {
    "ghl_health_percentage": 95.74,
    "webhook_health_percentage": 93.75,
    "overall_health": 94.75
  }
}
```

### Alertas Automáticas

El sistema registra automáticamente:

- **Rate Limit Bajo**: Cuando quedan < 10 requests
- **Tokens Expirados**: Refresh automático con logging
- **Errores de Validación**: Por tipo de validación
- **Webhooks Fallidos**: Con detalles del error

### Logs Estructurados

Todos los logs incluyen contexto completo:

```json
{
  "timestamp": "2025-12-22T15:30:45.123Z",
  "session_id": "a1b2c3d4",
  "operation": "create_appointment",
  "success": true,
  "duration_ms": 234.5,
  "appointment_id": "ghl_123",
  "calendar_id": "cal_456",
  "details": {
    "attempt": 1,
    "rate_limit_remaining": "45"
  }
}
```

---

## 🔍 Troubleshooting

### Problemas Comunes

#### 1. Error 401/403 - Token Expirado

**Síntomas:**
```json
{"error": "Authentication failed - unable to refresh token"}
```

**Solución:**
1. Verificar variables de entorno GHL
2. Regenerar tokens en GHL Developer Portal
3. Actualizar `.env` con nuevos tokens

#### 2. Error 429 - Rate Limit

**Síntomas:**
```
Rate limited (attempt 1/3), waiting 2.34s
```

**Solución:**
- El sistema maneja automáticamente con backoff exponencial
- Verificar métricas: `GET /api/ghl/metrics/ghl/`
- Reducir frecuencia de operaciones si es necesario

#### 3. Webhooks Duplicados

**Síntomas:**
```
Webhook webhook_123 ya procesado, ignorando
```

**Solución:**
- Comportamiento normal (idempotencia funcionando)
- Verificar métricas de webhooks para confirmar

#### 4. Validación de Overlaps

**Síntomas:**
```json
{"non_field_errors": ["Conflicto de horario con: Cita Existente (14:00 - 15:00)"]}
```

**Solución:**
1. Verificar horarios disponibles
2. Usar modo de validación flexible:
   ```python
   # En el contexto del serializer
   context = {'strict_validation': False}
   ```

#### 5. Calendario No Disponible

**Síntomas:**
```json
{"non_field_errors": ["El calendario cal_123 no existe o no está disponible"]}
```

**Solución:**
1. Verificar calendarios: `GET /api/ghl/calendars/`
2. Sincronizar calendarios: `POST /api/locations/settings/{id}/sync_calendars/`
3. Actualizar calendar_id en la configuración

### Comandos de Diagnóstico

```bash
# 1. Verificar salud del sistema
curl -X GET "http://localhost:8000/api/ghl/health/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 2. Ver métricas detalladas
curl -X GET "http://localhost:8000/api/ghl/metrics/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 3. Probar conexión con GHL
python test_ghl.py

# 4. Verificar configuración
python manage.py shell
>>> from django.conf import settings
>>> print(f"GHL_LOCATION_ID: {settings.GHL_LOCATION_ID}")
>>> print(f"GHL_ACCESS_TOKEN: {settings.GHL_ACCESS_TOKEN[:20]}...")
```

---

## 🧪 Testing

### Colección Postman

Importar la colección completa:
- Archivo: `docs/Reflexo_GHL_Integration.postman_collection.json`
- Variables requeridas: `base_url`, `jwt_token`, `ghl_location_id`

### Tests Automatizados

```bash
# Ejecutar todos los tests
python manage.py test appointments.tests

# Tests específicos
python manage.py test appointments.tests.test_integration_e2e

# Tests con coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

### Escenarios de Prueba

1. **E2E Completo**: Crear → Actualizar → Cancelar
2. **Webhooks**: Simular eventos desde GHL
3. **Validaciones**: Overlaps, horarios, duraciones
4. **Idempotencia**: Webhooks duplicados
5. **Rate Limits**: Manejo de límites de API

---

## ⚠️ Códigos de Error

### Errores HTTP

| Código | Descripción | Solución |
|--------|-------------|----------|
| 400 | Bad Request - Datos inválidos | Verificar formato de datos |
| 401 | Unauthorized - Token inválido | Renovar JWT token |
| 403 | Forbidden - Sin permisos | Verificar permisos de usuario |
| 404 | Not Found - Recurso no existe | Verificar ID del recurso |
| 429 | Too Many Requests - Rate limit | Esperar o reducir frecuencia |
| 500 | Internal Server Error | Revisar logs del servidor |

### Errores de Validación

| Error | Causa | Solución |
|-------|-------|----------|
| `Conflicto de horario` | Overlap detectado | Cambiar horario o usar validación flexible |
| `Horario fuera del horario de trabajo` | Fuera de 8 AM - 8 PM | Ajustar horario |
| `La duración mínima es 15 minutos` | Cita muy corta | Aumentar duración |
| `El calendario no existe` | Calendar ID inválido | Verificar calendarios disponibles |

### Errores de GHL

| Error | Causa | Solución |
|-------|-------|----------|
| `Authentication failed` | Token expirado | Refresh automático o manual |
| `Calendar not found` | Calendar ID inválido | Sincronizar calendarios |
| `Contact not found` | Contact ID inválido | Verificar contacto en GHL |
| `Location not accessible` | Location ID inválido | Verificar permisos de location |

---

## 📞 Soporte

### Logs Importantes

```bash
# Logs de aplicación
tail -f logs/django.log

# Logs de GHL operations
grep "GHL_OPERATION" logs/django.log

# Logs de webhooks
grep "WEBHOOK_EVENT" logs/django.log

# Logs de validación
grep "VALIDATION_ERROR" logs/django.log
```

### Contacto

- **Equipo de Desarrollo**: Reflexo V3 Team
- **Documentación**: Este archivo README_OPERATIVO.md
- **Issues**: Reportar en el repositorio del proyecto

---

**Última actualización**: 22 de diciembre de 2025  
**Versión**: 1.0.0  
**Estado**: Producción Ready ✅