import httpx
import time
import random
from functools import wraps
from django.conf import settings
from django.core.cache import cache
from rest_framework.exceptions import APIException
from utils.logging_utils import StructuredLogger
import logging

logger = logging.getLogger(__name__)

class TokenManager:
    """Maneja refresh automático de tokens GHL"""
    
    @staticmethod
    def refresh_token():
        """Refresh del access token usando refresh token"""
        structured_logger = StructuredLogger('integrations.ghl')
        start_time = time.time()
        
        try:
            refresh_token = getattr(settings, 'GHL_REFRESH_TOKEN', '')
            client_id = getattr(settings, 'GHL_CLIENT_ID', '')
            client_secret = getattr(settings, 'GHL_CLIENT_SECRET', '')
            
            if not all([refresh_token, client_id, client_secret]):
                logger.error("Missing GHL OAuth credentials for token refresh")
                return False
            
            url = "https://services.leadconnectorhq.com/oauth/token"
            data = {
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            }
            
            with httpx.Client() as client:
                response = client.post(url, data=data, timeout=10.0)
                response.raise_for_status()
                
                token_data = response.json()
                new_access_token = token_data.get('access_token')
                new_refresh_token = token_data.get('refresh_token')
                
                if new_access_token:
                    # Actualizar tokens en cache (en producción usar variables de entorno)
                    cache.set('ghl_access_token', new_access_token, timeout=3600)
                    if new_refresh_token:
                        cache.set('ghl_refresh_token', new_refresh_token, timeout=86400)
                    
                    duration = (time.time() - start_time) * 1000
                    structured_logger.log_ghl_operation(
                        'refresh_token', True, 
                        {'token_length': len(new_access_token)}, 
                        duration
                    )
                    
                    logger.info("GHL tokens refreshed successfully")
                    return True
                    
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            structured_logger.log_ghl_operation(
                'refresh_token', False, 
                {'error': str(e)}, 
                duration
            )
            logger.error(f"Error refreshing GHL token: {str(e)}")
            return False
        
        return False
    
    @staticmethod
    def get_current_token():
        """Obtiene el token actual (cache o settings)"""
        cached_token = cache.get('ghl_access_token')
        if cached_token:
            return cached_token
        return getattr(settings, 'GHL_ACCESS_TOKEN', '')

def with_token_refresh_and_backoff(max_retries=3):
    """Decorator para manejo automático de tokens y backoff"""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            structured_logger = StructuredLogger('integrations.ghl')
            
            for attempt in range(max_retries):
                start_time = time.time()
                
                try:
                    # Actualizar token antes de la llamada
                    self.access_token = TokenManager.get_current_token()
                    
                    response = func(self, *args, **kwargs)
                    
                    # Log rate limit headers si están disponibles
                    if hasattr(response, 'headers'):
                        remaining = response.headers.get('X-RateLimit-Remaining')
                        reset_time = response.headers.get('X-RateLimit-Reset')
                        if remaining:
                            logger.info(f"Rate limit remaining: {remaining}")
                            if int(remaining) < 10:
                                logger.warning(f"Rate limit low: {remaining} requests remaining")
                    
                    # Log operación exitosa
                    duration = (time.time() - start_time) * 1000
                    structured_logger.log_ghl_operation(
                        func.__name__, True,
                        {
                            'attempt': attempt + 1,
                            'rate_limit_remaining': response.headers.get('X-RateLimit-Remaining') if hasattr(response, 'headers') else None
                        },
                        duration
                    )
                    
                    return response
                    
                except httpx.HTTPStatusError as e:
                    duration = (time.time() - start_time) * 1000
                    
                    if e.response.status_code == 429:
                        # Rate limit - backoff exponencial con jitter
                        delay = (2 ** attempt) + random.uniform(0, 1)
                        logger.warning(f"Rate limited (attempt {attempt + 1}/{max_retries}), waiting {delay:.2f}s")
                        
                        structured_logger.log_ghl_operation(
                            func.__name__, False,
                            {
                                'error': 'rate_limited',
                                'attempt': attempt + 1,
                                'delay': delay,
                                'status_code': e.response.status_code
                            },
                            duration
                        )
                        
                        time.sleep(delay)
                        continue
                        
                    elif e.response.status_code in [401, 403]:
                        # Token expirado - intentar refresh
                        logger.info(f"Token expired (attempt {attempt + 1}/{max_retries}), refreshing...")
                        
                        structured_logger.log_ghl_operation(
                            func.__name__, False,
                            {
                                'error': 'token_expired',
                                'attempt': attempt + 1,
                                'status_code': e.response.status_code
                            },
                            duration
                        )
                        
                        if TokenManager.refresh_token():
                            continue
                        else:
                            logger.error("Failed to refresh token")
                            raise APIException("Authentication failed - unable to refresh token")
                    
                    elif e.response.status_code >= 500:
                        # Error del servidor - backoff
                        delay = (2 ** attempt) + random.uniform(0, 1)
                        logger.warning(f"Server error {e.response.status_code} (attempt {attempt + 1}/{max_retries}), waiting {delay:.2f}s")
                        
                        structured_logger.log_ghl_operation(
                            func.__name__, False,
                            {
                                'error': 'server_error',
                                'attempt': attempt + 1,
                                'delay': delay,
                                'status_code': e.response.status_code
                            },
                            duration
                        )
                        
                        time.sleep(delay)
                        continue
                    else:
                        # Otros errores HTTP
                        structured_logger.log_ghl_operation(
                            func.__name__, False,
                            {
                                'error': 'http_error',
                                'status_code': e.response.status_code,
                                'response_text': e.response.text[:200]
                            },
                            duration
                        )
                        
                        logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
                        raise APIException(f"GHL API error: {e.response.status_code}")
                        
                except httpx.RequestError as e:
                    # Errores de conexión
                    duration = (time.time() - start_time) * 1000
                    delay = (2 ** attempt) + random.uniform(0, 1)
                    
                    structured_logger.log_ghl_operation(
                        func.__name__, False,
                        {
                            'error': 'connection_error',
                            'attempt': attempt + 1,
                            'delay': delay,
                            'error_details': str(e)
                        },
                        duration
                    )
                    
                    logger.warning(f"Connection error (attempt {attempt + 1}/{max_retries}): {str(e)}, waiting {delay:.2f}s")
                    time.sleep(delay)
                    continue
            
            # Si llegamos aquí, se agotaron los reintentos
            structured_logger.log_ghl_operation(
                func.__name__, False,
                {'error': 'max_retries_exceeded', 'max_retries': max_retries},
                0
            )
            
            raise APIException(f"Max retries ({max_retries}) exceeded")
        return wrapper
    return decorator

class GHLClient:
    """Cliente para interactuar con GoHighLevel API V2"""
    
    def __init__(self):
        self.base_url = "https://services.leadconnectorhq.com"
        self.access_token = TokenManager.get_current_token()
        self.location_id = getattr(settings, 'GHL_LOCATION_ID', '')
        self.structured_logger = StructuredLogger('integrations.ghl')
    
    def _get_headers(self):
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Version": "2021-07-28",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    @with_token_refresh_and_backoff()
    def create_appointment(self, data):
        """
        Creates an appointment in GHL
        Ref: https://highlevel.stoplight.io/docs/integrations/0091c9d2f2604-create-appointment
        """
        url = f"{self.base_url}/calendars/events/appointments"
        
        try:
            with httpx.Client() as client:
                response = client.post(
                    url, 
                    json=data, 
                    headers=self._get_headers(),
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"GHL Create Appointment Error: {str(e)}")
            if hasattr(e, 'response') and e.response:
                 logger.error(f"GHL Response: {e.response.text}")
            raise APIException(f"Error communicating with GHL: {str(e)}")

    @with_token_refresh_and_backoff()
    def update_appointment(self, appointment_id, data):
        url = f"{self.base_url}/calendars/events/appointments/{appointment_id}"
        try:
            with httpx.Client() as client:
                response = client.put(
                    url, 
                    json=data, 
                    headers=self._get_headers(),
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"GHL Update Appointment Error: {str(e)}")
            raise APIException(f"Error communicating with GHL: {str(e)}")

    @with_token_refresh_and_backoff()
    def cancel_appointment(self, appointment_id):
        """
        GHL API requires UPDATE with status 'cancelled' usually, or DELETE.
        Checking docs: DELETE /calendars/events/appointments/{appointmentId}
        """
        url = f"{self.base_url}/calendars/events/appointments/{appointment_id}"
        try:
            with httpx.Client() as client:
                response = client.delete(
                    url, 
                    headers=self._get_headers(),
                    timeout=10.0
                )
                response.raise_for_status()
                return True
        except httpx.HTTPError as e:
            logger.error(f"GHL Cancel Appointment Error: {str(e)}")
            raise APIException(f"Error communicating with GHL: {str(e)}")

    @with_token_refresh_and_backoff()
    def get_calendars(self, location_id=None):
        """Obtiene calendarios de una location"""
        url = f"{self.base_url}/calendars/"
        params = {'locationId': location_id or self.location_id}
        
        try:
            with httpx.Client() as client:
                response = client.get(
                    url, 
                    params=params, 
                    headers=self._get_headers(),
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"GHL Get Calendars Error: {str(e)}")
            raise APIException(f"Error getting calendars from GHL: {str(e)}")

ghl_client = GHLClient()
