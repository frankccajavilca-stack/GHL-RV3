from datetime import datetime
import pytz
from django.utils import timezone as django_timezone

LIMA_TZ = pytz.timezone('America/Lima')
UTC_TZ = pytz.UTC

def to_lima_time(dt):
    """
    Convierte datetime UTC a hora Lima
    
    Args:
        dt: datetime object (aware o naive)
        
    Returns:
        datetime object en timezone Lima
    """
    if dt is None:
        return None
    
    # Si es naive, asumimos UTC
    if dt.tzinfo is None:
        dt = UTC_TZ.localize(dt)
    
    return dt.astimezone(LIMA_TZ)


def normalize_datetime(dt):
    """
    Normaliza datetime a UTC para guardar en DB
    
    Args:
        dt: datetime object o string ISO
        
    Returns:
        datetime object en UTC timezone-aware
    """
    if dt is None:
        return None
    
    # Si es string, parsear
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except ValueError:
            # Fallback para formatos sin offset
            dt = datetime.fromisoformat(dt)
    
    # Si es naive, asumimos Lima
    if dt.tzinfo is None:
        dt = LIMA_TZ.localize(dt)
    
    return dt.astimezone(UTC_TZ)


def to_utc_iso(dt):
    """
    Convierte datetime a string ISO en UTC
    
    Args:
        dt: datetime object
        
    Returns:
        String ISO format (ej: "2025-11-15T14:30:00.000Z")
    """
    if dt is None:
        return None
    
    # Convertir a UTC si no lo está
    if dt.tzinfo != UTC_TZ:
        dt = dt.astimezone(UTC_TZ)
    
    return dt.isoformat().replace('+00:00', 'Z')


def get_current_lima_time():
    """Retorna datetime actual en timezone Lima"""
    return django_timezone.now().astimezone(LIMA_TZ)
