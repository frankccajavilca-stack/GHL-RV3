from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from utils.logging_utils import MetricsCollector
import logging

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_system_metrics(request):
    """
    Endpoint para obtener métricas del sistema
    
    Returns:
        - GHL operations metrics
        - Webhook processing metrics
        - Validation error metrics
        - System health overview
    """
    try:
        metrics_data = {
            'ghl_operations': MetricsCollector.get_ghl_metrics(),
            'webhooks': MetricsCollector.get_webhook_metrics(),
            'validations': MetricsCollector.get_validation_metrics(),
            'system_health': MetricsCollector.get_system_health(),
            'timestamp': None  # Will be set by serializer
        }
        
        from django.utils import timezone
        metrics_data['timestamp'] = timezone.now().isoformat()
        
        return Response({
            'metrics': metrics_data,
            'success': True
        })
        
    except Exception as e:
        logger.error(f"Error fetching metrics: {str(e)}", exc_info=True)
        return Response(
            {
                'error': 'Error obteniendo métricas',
                'details': str(e),
                'success': False
            },
            status=500
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_ghl_metrics(request):
    """Endpoint específico para métricas de GHL"""
    try:
        metrics = MetricsCollector.get_ghl_metrics()
        return Response({
            'metrics': metrics,
            'success': True
        })
    except Exception as e:
        logger.error(f"Error fetching GHL metrics: {str(e)}")
        return Response({'error': str(e), 'success': False}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_webhook_metrics(request):
    """Endpoint específico para métricas de webhooks"""
    try:
        metrics = MetricsCollector.get_webhook_metrics()
        return Response({
            'metrics': metrics,
            'success': True
        })
    except Exception as e:
        logger.error(f"Error fetching webhook metrics: {str(e)}")
        return Response({'error': str(e), 'success': False}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_system_health(request):
    """Endpoint para health check del sistema"""
    try:
        health = MetricsCollector.get_system_health()
        
        # Determinar status basado en salud general
        overall_health = health['overall_health']
        if overall_health >= 95:
            status_text = 'healthy'
        elif overall_health >= 80:
            status_text = 'degraded'
        else:
            status_text = 'unhealthy'
        
        return Response({
            'status': status_text,
            'health': health,
            'success': True
        })
    except Exception as e:
        logger.error(f"Error fetching system health: {str(e)}")
        return Response({
            'status': 'unknown',
            'error': str(e),
            'success': False
        }, status=500)