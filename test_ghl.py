"""
Script para probar conexión con GHL
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.settings')

import django
django.setup()

from django.conf import settings
import httpx

def test_ghl_connection():
    headers = {
        'Authorization': f'Bearer {settings.GHL_ACCESS_TOKEN}',
        'Version': '2021-07-28',
        'Content-Type': 'application/json'
    }
    
    print("=" * 50)
    print("PRUEBA DE CONEXION CON GHL")
    print("=" * 50)
    print(f"Location ID: {settings.GHL_LOCATION_ID}")
    print()
    
    # Test 1: Obtener calendarios
    try:
        r = httpx.get(
            f'https://services.leadconnectorhq.com/calendars/?locationId={settings.GHL_LOCATION_ID}',
            headers=headers,
            timeout=15
        )
        print(f"Status: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            calendars = data.get('calendars', [])
            print(f"Total calendarios: {len(calendars)}")
            print()
            for cal in calendars:
                print(f"  - {cal.get('name', 'N/A')}")
                print(f"    ID: {cal.get('id', 'N/A')}")
                print()
        else:
            print(f"Error: {r.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    test_ghl_connection()
