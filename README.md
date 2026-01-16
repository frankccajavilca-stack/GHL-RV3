# Proyecto Integrador RV3 ↔ GHL

Sincronización bidireccional entre Reflexo V3 y GoHighLevel.

## Características

- Sincronización automática de citas RV3 ↔ GHL
- Webhooks con idempotencia fuerte
- Cliente GHL robusto con manejo de tokens
- Sistema de validaciones y métricas
- Endpoints DRF completos

## Documentación

- `README_OPERATIVO.md` - Guía completa de uso
- `COMO_USAR.md` - Instrucciones paso a paso
- `docs/Reflexo_GHL_Integration.postman_collection.json` - Colección Postman

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
