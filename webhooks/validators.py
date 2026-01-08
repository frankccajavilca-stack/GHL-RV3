import hmac
import hashlib
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def validate_ghl_signature(request) -> bool:
    """
    Valida la firma del webhook de GHL
    
    Args:
        request: Django request object
        
    Returns:
        bool: True si la firma es válida
    """
    signature = request.headers.get('X-GHL-Signature', '')
    
    if not signature:
        logger.warning("No GHL signature found in webhook request")
        return False
    
    webhook_secret = getattr(settings, 'GHL_WEBHOOK_SECRET', '')
    
    if not webhook_secret:
        logger.warning("GHL_WEBHOOK_SECRET not configured")
        return True  # Skip validation if not configured
    
    # Calcular firma esperada
    payload = request.body
    expected_signature = hmac.new(
        webhook_secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    is_valid = hmac.compare_digest(signature, expected_signature)
    
    if not is_valid:
        logger.warning("Invalid GHL webhook signature")
    
    return is_valid
