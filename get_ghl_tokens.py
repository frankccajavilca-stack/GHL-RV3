"""
Script helper para obtener tokens de GHL via OAuth
"""
import requests
import json
from urllib.parse import urlencode

def get_authorization_url(client_id, redirect_uri):
    """
    Genera URL de autorización para GHL OAuth
    """
    base_url = "https://marketplace.gohighlevel.com/oauth/chooselocation"
    
    params = {
        'response_type': 'code',
        'redirect_uri': redirect_uri,
        'client_id': client_id,
        'scope': 'calendars.readonly calendars.write calendars/events.readonly calendars/events.write contacts.readonly contacts.write locations.readonly'
    }
    
    auth_url = f"{base_url}?{urlencode(params)}"
    return auth_url

def exchange_code_for_tokens(client_id, client_secret, code, redirect_uri):
    """
    Intercambia código de autorización por tokens
    """
    url = "https://services.leadconnectorhq.com/oauth/token"
    
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri
    }
    
    response = requests.post(url, data=data)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

def main():
    """
    Proceso interactivo para obtener tokens
    """
    print("🔑 OBTENER TOKENS DE GHL")
    print("=" * 40)
    
    # Paso 1: Configuración
    client_id = input("Ingresa tu GHL_CLIENT_ID: ").strip()
    client_secret = input("Ingresa tu GHL_CLIENT_SECRET: ").strip()
    redirect_uri = "http://localhost:8000/oauth/callback"  # Puedes usar esta URL
    
    # Paso 2: URL de autorización
    auth_url = get_authorization_url(client_id, redirect_uri)
    
    print(f"\n📋 PASO 1: Autorización")
    print("Abre esta URL en tu navegador:")
    print(f"{auth_url}")
    print("\nDespués de autorizar, serás redirigido a una URL como:")
    print("http://localhost:8000/oauth/callback?code=CODIGO_AQUI&location_id=LOCATION_ID")
    
    # Paso 3: Obtener código
    print(f"\n📋 PASO 2: Código de autorización")
    code = input("Pega el CODIGO de la URL de redirección: ").strip()
    location_id = input("Pega el LOCATION_ID de la URL: ").strip()
    
    # Paso 4: Intercambiar por tokens
    print(f"\n📋 PASO 3: Obteniendo tokens...")
    tokens = exchange_code_for_tokens(client_id, client_secret, code, redirect_uri)
    
    if tokens:
        print("\n✅ ¡Tokens obtenidos exitosamente!")
        print("\n📝 Actualiza tu archivo .env con estos valores:")
        print("=" * 50)
        print(f"GHL_CLIENT_ID={client_id}")
        print(f"GHL_CLIENT_SECRET={client_secret}")
        print(f"GHL_ACCESS_TOKEN={tokens.get('access_token', '')}")
        print(f"GHL_REFRESH_TOKEN={tokens.get('refresh_token', '')}")
        print(f"GHL_LOCATION_ID={location_id}")
        print(f"GHL_WEBHOOK_SECRET=tu_webhook_secret_opcional")
        print("=" * 50)
        
        # Guardar en archivo
        with open('.env.ghl_tokens', 'w') as f:
            f.write(f"GHL_CLIENT_ID={client_id}\n")
            f.write(f"GHL_CLIENT_SECRET={client_secret}\n")
            f.write(f"GHL_ACCESS_TOKEN={tokens.get('access_token', '')}\n")
            f.write(f"GHL_REFRESH_TOKEN={tokens.get('refresh_token', '')}\n")
            f.write(f"GHL_LOCATION_ID={location_id}\n")
            f.write(f"GHL_WEBHOOK_SECRET=tu_webhook_secret_opcional\n")
        
        print(f"\n💾 Tokens guardados en: .env.ghl_tokens")
        print("Copia estas líneas a tu archivo .env principal")
        
    else:
        print("\n❌ Error obteniendo tokens")
        print("Verifica que el código y las credenciales sean correctos")

if __name__ == '__main__':
    main()