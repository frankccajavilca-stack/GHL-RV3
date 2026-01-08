import logging
import json
import time
from datetime import datetime, timedelta
from functools import wraps
from django.core.cache import cache
from django.conf import settings
import uuid

class StructuredLogger:
    """
    Logger estructurado para operaciones GHL y métricas
    """
    
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        self.session_id = str(uuid.uuid4())[:8]
    
    def log_ghl_operation(self, operation, success, details=None, duration=None, 
                         appointment_id=None, calendar_id=None):
        """
        Log estructurado para operaciones GHL
        
        Args:
            operation: Nombre de la operación (create_appointment, update_appointment, etc.)
            success: Si la operación fue exitosa
            details: Detalles adicionales
            duration: Duración en milisegundos
            appointment_id: ID de la cita
            calendar_id: ID del calendario
        """
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'session_id': self.session_id,
            'operation': operation,
            'success': success,
            'duration_ms': duration,
            'appointment_id': appointment_id,
            'calendar_id': calendar_id,
            'details': details or {}
        }
        
        # Agregar contexto adicional
        if hasattr(settings, 'GHL_LOCATION_ID'):
            log_data['location_id'] = settings.GHL_LOCATION_ID
        
        log_message = f"GHL_OPERATION: {json.dumps(log_data, default=str)}"
        
        if success:
            self.logger.info(log_message)
        else:
            self.logger.error(log_message)
        
        # Actualizar métricas en cache
        self._update_metrics(operation, success, duration)
    
    def log_webhook_event(self, event_type, success, webhook_id=None, 
                         appointment_id=None, details=None):
        """
        Log estructurado para eventos de webhook
        """
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'session_id': self.session_id,
            'event_type': event_type,
            'webhook_id': webhook_id,
            'appointment_id': appointment_id,
            'success': success,
            'details': details or {}
        }
        
        log_message = f"WEBHOOK_EVENT: {json.dumps(log_data, default=str)}"
        
        if success:
            self.logger.info(log_message)
        else:
            self.logger.error(log_message)
        
        # Actualizar métricas de webhooks
        self._update_webhook_metrics(event_type, success)
    
    def log_validation_error(self, validation_type, error_details, 
                           appointment_data=None):
        """
        Log para errores de validación
        """
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'session_id': self.session_id,
            'validation_type': validation_type,
            'error_details': error_details,
            'appointment_data': appointment_data or {}
        }
        
        log_message = f"VALIDATION_ERROR: {json.dumps(log_data, default=str)}"
        self.logger.warning(log_message)
        
        # Actualizar métricas de validación
        self._update_validation_metrics(validation_type)
    
    def _update_metrics(self, operation, success, duration=None):
        """Actualiza contadores de métricas en cache"""
        try:
            # Contadores básicos
            key_success = f"ghl_metrics:{operation}:success"
            key_failed = f"ghl_metrics:{operation}:failed"
            key_total = f"ghl_metrics:{operation}:total"
            
            # Incrementar contadores
            if success:
                cache.set(key_success, cache.get(key_success, 0) + 1, timeout=3600)
            else:
                cache.set(key_failed, cache.get(key_failed, 0) + 1, timeout=3600)
            
            cache.set(key_total, cache.get(key_total, 0) + 1, timeout=3600)
            
            # Métricas de duración (solo para operaciones exitosas)
            if success and duration is not None:
                key_duration = f"ghl_metrics:{operation}:avg_duration"
                key_duration_count = f"ghl_metrics:{operation}:duration_count"
                
                current_avg = cache.get(key_duration, 0)
                current_count = cache.get(key_duration_count, 0)
                
                # Calcular nueva media
                new_count = current_count + 1
                new_avg = ((current_avg * current_count) + duration) / new_count
                
                cache.set(key_duration, new_avg, timeout=3600)
                cache.set(key_duration_count, new_count, timeout=3600)
            
        except Exception as e:
            self.logger.error(f"Error updating metrics: {e}")
    
    def _update_webhook_metrics(self, event_type, success):
        """Actualiza métricas de webhooks"""
        try:
            key_success = f"webhook_metrics:{event_type}:success"
            key_failed = f"webhook_metrics:{event_type}:failed"
            
            if success:
                cache.set(key_success, cache.get(key_success, 0) + 1, timeout=3600)
            else:
                cache.set(key_failed, cache.get(key_failed, 0) + 1, timeout=3600)
                
        except Exception as e:
            self.logger.error(f"Error updating webhook metrics: {e}")
    
    def _update_validation_metrics(self, validation_type):
        """Actualiza métricas de validación"""
        try:
            key = f"validation_metrics:{validation_type}:errors"
            cache.set(key, cache.get(key, 0) + 1, timeout=3600)
        except Exception as e:
            self.logger.error(f"Error updating validation metrics: {e}")


class MetricsCollector:
    """
    Recolector de métricas del sistema
    """
    
    @staticmethod
    def get_ghl_metrics():
        """Obtiene métricas de operaciones GHL"""
        operations = ['create_appointment', 'update_appointment', 'cancel_appointment', 'get_calendars']
        metrics = {}
        
        for operation in operations:
            success_count = cache.get(f"ghl_metrics:{operation}:success", 0)
            failed_count = cache.get(f"ghl_metrics:{operation}:failed", 0)
            total_count = cache.get(f"ghl_metrics:{operation}:total", 0)
            avg_duration = cache.get(f"ghl_metrics:{operation}:avg_duration", 0)
            
            success_rate = (success_count / total_count * 100) if total_count > 0 else 0
            
            metrics[operation] = {
                'success_count': success_count,
                'failed_count': failed_count,
                'total_count': total_count,
                'success_rate': round(success_rate, 2),
                'avg_duration_ms': round(avg_duration, 2) if avg_duration else 0
            }
        
        return metrics
    
    @staticmethod
    def get_webhook_metrics():
        """Obtiene métricas de webhooks"""
        event_types = ['AppointmentCreate', 'AppointmentUpdate', 'AppointmentDelete']
        metrics = {}
        
        for event_type in event_types:
            success_count = cache.get(f"webhook_metrics:{event_type}:success", 0)
            failed_count = cache.get(f"webhook_metrics:{event_type}:failed", 0)
            total_count = success_count + failed_count
            
            success_rate = (success_count / total_count * 100) if total_count > 0 else 0
            
            metrics[event_type] = {
                'success_count': success_count,
                'failed_count': failed_count,
                'total_count': total_count,
                'success_rate': round(success_rate, 2)
            }
        
        return metrics
    
    @staticmethod
    def get_validation_metrics():
        """Obtiene métricas de validación"""
        validation_types = ['overlap', 'business_hours', 'duration', 'calendar_availability']
        metrics = {}
        
        for validation_type in validation_types:
            error_count = cache.get(f"validation_metrics:{validation_type}:errors", 0)
            metrics[validation_type] = {
                'error_count': error_count
            }
        
        return metrics
    
    @staticmethod
    def get_system_health():
        """Obtiene métricas generales de salud del sistema"""
        ghl_metrics = MetricsCollector.get_ghl_metrics()
        webhook_metrics = MetricsCollector.get_webhook_metrics()
        
        # Calcular salud general
        total_ghl_operations = sum(m['total_count'] for m in ghl_metrics.values())
        total_ghl_success = sum(m['success_count'] for m in ghl_metrics.values())
        
        total_webhook_events = sum(m['total_count'] for m in webhook_metrics.values())
        total_webhook_success = sum(m['success_count'] for m in webhook_metrics.values())
        
        ghl_health = (total_ghl_success / total_ghl_operations * 100) if total_ghl_operations > 0 else 100
        webhook_health = (total_webhook_success / total_webhook_events * 100) if total_webhook_events > 0 else 100
        
        return {
            'ghl_health_percentage': round(ghl_health, 2),
            'webhook_health_percentage': round(webhook_health, 2),
            'total_ghl_operations': total_ghl_operations,
            'total_webhook_events': total_webhook_events,
            'overall_health': round((ghl_health + webhook_health) / 2, 2)
        }


def log_execution_time(logger_name='default'):
    """
    Decorator para loggear tiempo de ejecución de funciones
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = StructuredLogger(logger_name)
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = (time.time() - start_time) * 1000
                
                logger.log_ghl_operation(
                    operation=func.__name__,
                    success=True,
                    duration=duration,
                    details={'function': f"{func.__module__}.{func.__name__}"}
                )
                
                return result
                
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                
                logger.log_ghl_operation(
                    operation=func.__name__,
                    success=False,
                    duration=duration,
                    details={
                        'function': f"{func.__module__}.{func.__name__}",
                        'error': str(e)
                    }
                )
                
                raise
        
        return wrapper
    return decorator