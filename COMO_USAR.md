# 🚀 Cómo Usar el Sistema - Reflexo V3 ↔ GHL Integration

## 📋 Guía Paso a Paso para Configurar y Usar

Esta guía te ayudará a configurar y usar el sistema de sincronización entre Reflexo V3 y GoHighLevel de manera sencilla.

---

## 🎯 ¿Qué hace este sistema?

✅ **Sincroniza citas automáticamente** entre Reflexo V3 y GoHighLevel  
✅ **Bidireccional**: Cambios en cualquier sistema se reflejan en el otro  
✅ **Tiempo real**: Sin necesidad de sincronización manual  
✅ **Robusto**: Maneja errores automáticamente  

---

## 🔧 PASO 1: Instalación Inicial

### 1.1 Requisitos Previos
```bash
# Verificar que tienes Python instalado
python --version  # Debe ser 3.9 o superior

# Verificar que tienes MySQL
mysql --version

# Instalar Redis (opcional, para métricas)
# Windows: Descargar desde https://redis.io/download
# Mac: brew install redis
# Linux: sudo apt-get install redis-server
```

### 1.2 Instalar Dependencias
```bash
# 1. Navegar al directorio del proyecto
cd Reflexo-V3-main

# 2. Instalar dependencias de Python
pip install -r requirements.txt

# 3. Configurar base de datos
python manage.py makemigrations
python manage.py migrate

# 4. Crear usuario administrador
python manage.py createsuperuser
```

---

## 🔑 PASO 2: Configurar GoHighLevel

### 2.1 Crear App en GHL (Solo la primera vez)

1. **Ir a GHL Marketplace**
   - URL: https://marketplace.gohighlevel.com/
   - Iniciar sesión con tu cuenta GHL

2. **Crear Nueva App**
   - Click en "Create App" o "Nueva Aplicación"
   - Nombre: "Reflexo V3 Integration"
   - Tipo: "Private App" (para uso personal)

3. **Configurar Permisos (Scopes)**
   ```
   ✅ calendars.readonly
   ✅ calendars.write
   ✅ calendars/events.readonly
   ✅ calendars/events.write
   ✅ contacts.readonly
   ✅ contacts.write
   ✅ locations.readonly
   ```

4. **Configurar Redirect URI**
   ```
   http://localhost:8000/oauth/callback
   ```

5. **Guardar y Obtener Credenciales**
   - Anota tu `CLIENT_ID` y `CLIENT_SECRET`

### 2.2 Obtener Tokens de Acceso

**Opción A: Usar Script Automático (Recomendado)**
```bash
python get_ghl_tokens.py
```

**Opción B: Proceso Manual**
1. Abrir esta URL en tu navegador (reemplaza TU_CLIENT_ID):
```
https://marketplace.gohighlevel.com/oauth/chooselocation?response_type=code&redirect_uri=http://localhost:8000/oauth/callback&client_id=TU_CLIENT_ID&scope=calendars.readonly calendars.write calendars/events.readonly calendars/events.write contacts.readonly contacts.write locations.readonly
```

2. Autorizar la aplicación
3. Copiar el `code` y `location_id` de la URL de redirección
4. Usar Postman para intercambiar por tokens:
```bash
POST https://services.leadconnectorhq.com/oauth/token
Content-Type: application/x-www-form-urlencoded

client_id=TU_CLIENT_ID
client_secret=TU_CLIENT_SECRET
grant_type=authorization_code
code=CODIGO_OBTENIDO
redirect_uri=http://localhost:8000/oauth/callback
```

---

## ⚙️ PASO 3: Configurar Variables de Entorno

### 3.1 Editar archivo .env

Abre el archivo `.env` en la raíz del proyecto y actualiza estas variables:

```bash
# ==================== GoHighLevel (GHL) - ACTUALIZAR ESTAS ====================
GHL_CLIENT_ID=tu_client_id_de_ghl
GHL_CLIENT_SECRET=tu_client_secret_de_ghl
GHL_ACCESS_TOKEN=tu_access_token_obtenido
GHL_REFRESH_TOKEN=tu_refresh_token_obtenido
GHL_LOCATION_ID=tu_location_id_de_ghl
GHL_WEBHOOK_SECRET=cualquier_string_aleatorio_opcional

# ==================== Otras configuraciones (mantener como están) ====================
FRONTEND_URL=http://localhost:3000
CORS_ALLOW_ALL_ORIGINS=True
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### 3.2 ¿Dónde encontrar cada valor?

| Variable | Dónde encontrarla |
|----------|-------------------|
| `GHL_CLIENT_ID` | Dashboard de tu app en GHL Marketplace |
| `GHL_CLIENT_SECRET` | Dashboard de tu app en GHL Marketplace |
| `GHL_ACCESS_TOKEN` | Resultado del proceso OAuth (Paso 2.2) |
| `GHL_REFRESH_TOKEN` | Resultado del proceso OAuth (Paso 2.2) |
| `GHL_LOCATION_ID` | URL de redirección OAuth o dashboard GHL |
| `GHL_WEBHOOK_SECRET` | Cualquier string (ej: `mi-webhook-secreto-123`) |

---

## 🚀 PASO 4: Iniciar el Sistema

### 4.1 Probar Configuración
```bash
# Probar conexión con GHL
python test_ghl.py
```

**Resultado esperado:**
```
==================================================
PRUEBA DE CONEXION CON GHL
==================================================
Location ID: tu_location_id
Status: 200
Total calendarios: 2

  - Fisioterapia
    ID: cal_123456

  - Consultas Generales  
    ID: cal_789012
```

### 4.2 Iniciar Servidor
```bash
python manage.py runserver
```

**Verificar que funciona:**
- Abrir: http://localhost:8000/health/
- Debe mostrar: `{"status": "healthy", "service": "reflexo-backend"}`

---

## 📱 PASO 5: Usar el Sistema

### 5.1 Obtener Token JWT (Para usar la API)

**Usando Postman:**
```bash
POST http://localhost:8000/api/architect/login/
Content-Type: application/json

{
    "username": "tu_usuario_admin",
    "password": "tu_password_admin"
}
```

**Respuesta:**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

Copia el `access` token para usar en las siguientes peticiones.

### 5.2 Probar Funcionalidades Básicas

#### A) Listar Calendarios Disponibles
```bash
GET http://localhost:8000/api/ghl/calendars/
Authorization: Bearer TU_JWT_TOKEN
```

#### B) Crear una Cita (se sincroniza automáticamente a GHL)
```bash
POST http://localhost:8000/api/ghl/citas/
Authorization: Bearer TU_JWT_TOKEN
Content-Type: application/json

{
    "title": "Consulta de Prueba",
    "contact_id": "contact_123",
    "ghl_calendar_id": "cal_456",
    "start_time": "2025-12-25T14:00:00-05:00",
    "end_time": "2025-12-25T15:00:00-05:00",
    "notes": "Primera prueba del sistema"
}
```

#### C) Ver Métricas del Sistema
```bash
GET http://localhost:8000/api/ghl/health/
Authorization: Bearer TU_JWT_TOKEN
```

---

## 📊 PASO 6: Importar Colección Postman (Recomendado)

### 6.1 Importar Colección
1. Abrir Postman
2. Click en "Import"
3. Seleccionar archivo: `docs/Reflexo_GHL_Integration.postman_collection.json`

### 6.2 Configurar Variables
En Postman, ir a la colección y configurar estas variables:

| Variable | Valor |
|----------|-------|
| `base_url` | `http://localhost:8000` |
| `jwt_token` | Tu token JWT obtenido en Paso 5.1 |
| `ghl_location_id` | Tu GHL_LOCATION_ID |
| `contact_id` | ID de un contacto existente en GHL |

### 6.3 Ejecutar Tests
1. Ejecutar "Login - Obtener JWT Token" primero
2. Luego ejecutar cualquier otro endpoint
3. La colección incluye tests automáticos

---

## 🔄 PASO 7: Configurar Webhooks (Opcional)

Para que los cambios en GHL se reflejen automáticamente en Reflexo V3:

### 7.1 En GHL Dashboard
1. Ir a Settings → Integrations → Webhooks
2. Crear nuevo webhook:
   - **URL**: `http://tu-servidor.com/api/webhooks/ghl/`
   - **Events**: Appointment Created, Updated, Deleted
   - **Secret**: El valor de `GHL_WEBHOOK_SECRET` de tu .env

### 7.2 Para Testing Local
Si quieres probar webhooks en desarrollo local:
1. Usar ngrok: `ngrok http 8000`
2. Usar la URL de ngrok en el webhook de GHL

---

## 🎯 Flujos de Uso Comunes

### Flujo 1: Crear Cita desde Reflexo V3
1. **Crear cita** usando API o interfaz
2. **Automáticamente** aparece en GHL
3. **Verificar** en el calendario de GHL

### Flujo 2: Modificar Cita desde GHL
1. **Editar cita** en el calendario de GHL
2. **Automáticamente** se actualiza en Reflexo V3
3. **Verificar** usando API de Reflexo V3

### Flujo 3: Monitorear Sistema
1. **Ver métricas**: `GET /api/ghl/metrics/`
2. **Health check**: `GET /api/ghl/health/`
3. **Ver logs** en la consola del servidor

---

## 🔍 Troubleshooting - Problemas Comunes

### ❌ Error: "Authentication failed"
**Causa**: Token de GHL expirado  
**Solución**: 
```bash
# El sistema intenta refresh automático, pero si falla:
# 1. Verificar GHL_REFRESH_TOKEN en .env
# 2. Regenerar tokens siguiendo Paso 2.2
```

### ❌ Error: "Calendar not found"
**Causa**: Calendar ID inválido  
**Solución**:
```bash
# Obtener calendarios válidos:
GET /api/ghl/calendars/
# Usar un ID de la respuesta
```

### ❌ Error: "Contact not found"
**Causa**: Contact ID no existe en GHL  
**Solución**:
```bash
# Usar un contact_id válido de tu GHL
# O crear contacto primero en GHL
```

### ❌ Error: "Rate limited"
**Causa**: Demasiadas peticiones a GHL  
**Solución**: 
```bash
# El sistema maneja automáticamente con backoff
# Esperar unos segundos y reintentar
```

### ❌ Error de conexión
**Causa**: Variables mal configuradas  
**Solución**:
```bash
# 1. Verificar .env
# 2. Probar conexión:
python test_ghl.py

# 3. Verificar que el servidor esté corriendo:
python manage.py runserver
```

---

## 📞 Soporte y Ayuda

### Logs Útiles
```bash
# Ver logs del servidor
# Los logs aparecen en la consola donde ejecutaste runserver

# Buscar errores específicos:
# - "GHL_OPERATION" para operaciones con GHL
# - "WEBHOOK_EVENT" para webhooks recibidos
# - "ERROR" para errores generales
```

### Comandos de Diagnóstico
```bash
# 1. Probar conexión GHL
python test_ghl.py

# 2. Verificar configuración
python manage.py shell
>>> from django.conf import settings
>>> print(settings.GHL_LOCATION_ID)

# 3. Ver métricas
curl http://localhost:8000/api/ghl/health/
```

### Archivos Importantes
- **`.env`** - Configuración principal
- **`test_ghl.py`** - Probar conexión GHL
- **`docs/Reflexo_GHL_Integration.postman_collection.json`** - Colección Postman
- **`README_OPERATIVO.md`** - Documentación técnica completa

---

## ✅ Checklist de Verificación

Antes de usar en producción, verifica:

- [ ] ✅ Variables de entorno configuradas correctamente
- [ ] ✅ `python test_ghl.py` funciona sin errores
- [ ] ✅ Servidor Django inicia correctamente
- [ ] ✅ Health check responde OK: `/health/`
- [ ] ✅ Puedes obtener JWT token
- [ ] ✅ Puedes listar calendarios: `/api/ghl/calendars/`
- [ ] ✅ Puedes crear una cita de prueba
- [ ] ✅ La cita aparece en GHL
- [ ] ✅ Métricas funcionan: `/api/ghl/metrics/`

---

## 🎉 ¡Listo para Usar!

Una vez completados todos los pasos, tu sistema estará funcionando y sincronizando automáticamente entre Reflexo V3 y GoHighLevel.

**Próximos pasos:**
1. Crear citas de prueba
2. Verificar sincronización
3. Configurar webhooks para sincronización completa
4. Monitorear métricas regularmente

---

**Última actualización**: 22 de diciembre de 2025  
**Versión**: 1.0.0  
**Soporte**: Equipo Reflexo V3