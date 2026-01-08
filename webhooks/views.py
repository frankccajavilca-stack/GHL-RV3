from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .handlers import WebhookHandler
from .validators import validate_ghl_signature
import logging

logger = logging.getLogger(__name__)


class GHLWebhookView(APIView):
    """
    Endpoint para recibir webhooks de GoHighLevel con idempotencia fuerte
    """
    permission_classes = [AllowAny]  # Los webhooks no tienen autenticación JWT
    
    def post(self, request):
        """
        Procesa eventos de webhook de GHL
        
        Expected payload structure:
        {
            "type": "AppointmentCreate" | "AppointmentUpdate" | "AppointmentDelete",
            "locationId": "...",
            "webhookId": "..." (opcional),
            "data": {
                "id": "...",
                "calendarId": "...",
                "contactId": "...",
                ...
            }
        }
        """
        # Validar firma (opcional, si GHL lo soporta)
        # if not validate_ghl_signature(request):
        #     return Response({'error': 'Invalid signature'}, status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            event_type = request.data.get('type')
            event_data = request.data.get('data', {})
            webhook_id = request.data.get('webhookId') or request.headers.get('X-Webhook-ID')
            
            if not event_type:
                return Response(
                    {'error': 'Missing event type'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not event_data.get('id'):
                return Response(
                    {'error': 'Missing appointment ID in data'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            logger.info(f"Webhook received: {event_type} for appointment {event_data.get('id')}")
            
            result = None
            if event_type == 'AppointmentCreate':
                result = WebhookHandler.handle_appointment_create(event_data, webhook_id)
            elif event_type == 'AppointmentUpdate':
                result = WebhookHandler.handle_appointment_update(event_data, webhook_id)
            elif event_type == 'AppointmentDelete':
                result = WebhookHandler.handle_appointment_delete(event_data, webhook_id)
            else:
                logger.warning(f"Unknown webhook event type: {event_type}")
                return Response(
                    {'error': f'Unknown event type: {event_type}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            response_data = {'status': 'ok', 'processed': True}
            if result:
                response_data['appointment_id'] = str(result.id)
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Webhook processing error: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Internal server error', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
