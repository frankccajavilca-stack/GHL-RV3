# Proyecto Integrador RV3 ↔ GHL

Sincronización bidireccional entre Reflexo V3 y GoHighLevel.

- [Diagramas del Proyecto](https://drive.google.com/drive/folders/1R-oAusPydEgCLrGjuXjmNNV-nueLvo4L?usp=sharing) - Diagramas de arquitectura y flujos

## Características

- Sincronización automática de citas RV3 ↔ GHL
- Webhooks con idempotencia fuerte
- Cliente GHL robusto con manejo de tokens
- Sistema de validaciones y métricas
- Endpoints DRF completos

## Estructura de Conexión GHL ↔ RV3

### Archivos principales de integración:

**Conexión con GHL:**
- `integrations/ghl_client.py` - Cliente GHL con manejo de tokens y API
- `appointments/services.py` - Servicio de sincronización RV3 → GHL
- `appointments/views.py` - Endpoints DRF para CRUD de citas
- `webhooks/handlers.py` - Procesamiento de webhooks GHL → RV3
- `webhooks/views.py` - Endpoint para recibir webhooks de GHL

**Modelos:**
- `appointments/models.py` - Modelo Cita con campos GHL
- `webhooks/models.py` - Modelo WebhookEvent para idempotencia
- `locations/models.py` - Configuración de calendarios por location

**Utilidades:**
- `utils/timezone_utils.py` - Manejo de timezone America/Lima
- `utils/logging_utils.py` - Logging estructurado y métricas


- [Diagramas del Proyecto](https://drive.google.com/drive/folders/1R-oAusPydEgCLrGjuXjmNNV-nueLvo4L?usp=sharing) - Diagramas de arquitectura y flujos

## Instalación

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Configuración

Configurar variables de entorno en `.env`:
- GHL_CLIENT_ID
- GHL_CLIENT_SECRET
- GHL_ACCESS_TOKEN
- GHL_REFRESH_TOKEN
- GHL_LOCATION_ID
