# Proyecto Integrador RV3 ↔ GoHighLevel (GHL)

- [Diagramas del Proyecto](https://drive.google.com/drive/folders/1R-oAusPydEgCLrGjuXjmNNV-nueLvo4L?usp=sharing) - Diagramas de arquitectura y flujos

## Descripción General del Sistema

Este proyecto implementa una **sincronización bidireccional automática** entre el sistema médico **Reflexo V3** y la plataforma de marketing **GoHighLevel (GHL)**. El sistema permite que las citas médicas se mantengan sincronizadas en tiempo real entre ambas plataformas, eliminando la necesidad de gestión manual duplicada.

### Funcionalidades Principales

- **Sincronización RV3 → GHL**: Las citas creadas, modificadas o canceladas en Reflexo V3 se reflejan automáticamente en GoHighLevel
- **Sincronización GHL → RV3**: Los cambios realizados en GoHighLevel (mediante webhooks) se actualizan automáticamente en Reflexo V3
- **Gestión de Calendarios**: Selección dinámica de calendarios por subcuenta/location de GHL
- **Validaciones Robustas**: Detección de conflictos de horario, validación de timezone (America/Lima) y verificación de datos
- **Idempotencia**: Sistema robusto que evita duplicados y maneja reintentos automáticamente
- **Autenticación OAuth 2.0**: Manejo automático de tokens con refresh y rate limiting

### Arquitectura del Sistema

El sistema está construido con una **arquitectura de microservicios** que incluye:

- **API REST**: Endpoints para gestión de citas con Django REST Framework
- **Cliente GHL**: Integración robusta con GoHighLevel API v2
- **Sistema de Webhooks**: Procesamiento de eventos en tiempo real desde GHL
- **Validaciones**: Servicios especializados para validación de datos y conflictos
- **Logging y Métricas**: Sistema completo de observabilidad y monitoreo

---

## Tecnologías Utilizadas

### Backend Framework
- **Django 5.2.5** - Framework web principal
- **Django REST Framework 3.14.0** - API REST
- **Django Simple JWT 5.3.0** - Autenticación JWT

### Base de Datos y Cache
- **SQLite3** - Base de datos por defecto (incluida con Django)
- **Redis 5.0.1** - Cache y broker de tareas (opcional)
- **MySQL 8.0** - Opción alternativa para producción

### Integración y Comunicación
- **HTTPX 0.25.0** - Cliente HTTP para GoHighLevel API
- **OAuth 2.0** - Autenticación con GoHighLevel
- **Webhooks** - Eventos en tiempo real desde GHL

### Procesamiento Asíncrono
- **Celery 5.3.4** - Tareas asíncronas
- **django-celery-beat 2.8.0** - Scheduler de tareas
- **django-celery-results 2.5.1** - Almacenamiento de resultados

### Utilidades y Herramientas
- **python-decouple 3.8** - Gestión de variables de entorno
- **pytz 2024.2** - Manejo de timezone (America/Lima)
- **django-cors-headers 4.3.1** - Configuración CORS
- **django-filter 23.5** - Filtros avanzados para API

### Deployment y Producción
- **Docker** - Containerización
- **Gunicorn 21.2.0** - Servidor WSGI
- **WhiteNoise 6.6.0** - Servicio de archivos estáticos
- **psycopg2-binary 2.9.9** - Conector PostgreSQL (opcional)

### Testing y Documentación
- **Postman** - Testing de API y documentación
- **Mermaid** - Diagramas UML
- **PlantUML** - Diagramas de casos de uso

---

## Guía de Instalación y Ejecución en Entorno Local

### Requisitos Previos

- **Python 3.9+** instalado
- **Git** para clonar el repositorio
- **Cuenta activa en GoHighLevel** con permisos de API
- **Redis** (opcional, solo si se requieren tareas asíncronas)

**Nota:** El proyecto usa SQLite3 por defecto, que viene incluido con Python. No se requiere instalación adicional de base de datos.

### 1. Clonar el Repositorio

```bash
git clone <URL_DEL_REPOSITORIO>
cd Reflexo-V3-main
```

### 2. Crear Entorno Virtual

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Windows:
venv\Scripts\activate
# En Linux/Mac:
source venv/bin/activate
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno

Crear archivo `.env` en la raíz del proyecto:

```bash
# Django
SECRET_KEY=tu_secret_key_aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# GoHighLevel (CRÍTICO - Obtener de GHL Developer Portal)
GHL_CLIENT_ID=tu_client_id_ghl
GHL_CLIENT_SECRET=tu_client_secret_ghl
GHL_ACCESS_TOKEN=tu_access_token_ghl
GHL_REFRESH_TOKEN=tu_refresh_token_ghl
GHL_LOCATION_ID=tu_location_id_ghl
GHL_WEBHOOK_SECRET=tu_webhook_secret

# Redis (opcional)
REDIS_URL=redis://localhost:6379/0

# CORS
CORS_ALLOW_ALL_ORIGINS=True
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

**Nota:** La base de datos SQLite3 (`db.sqlite3`) ya está configurada y no requiere configuración adicional.

### 5. Verificar Base de Datos

El proyecto incluye una base de datos SQLite3 preconfigurada (`db.sqlite3`) con todas las tablas y datos necesarios.

**No es necesario ejecutar migraciones** - La base de datos ya está lista para usar.

### 6. Crear Superusuario (Opcional)

Si necesitas acceso al panel de administración:

```bash
python manage.py createsuperuser
```

### 7. Probar Conexión con GHL

```bash
python test_ghl.py
```

**Resultado esperado:**
```
==================================================
PRUEBA DE CONEXION CON GHL
==================================================
Location ID: tu_location_id
Status: 200
Total calendarios: X

  - Nombre del Calendario
    ID: cal_123456
```

### 8. Ejecutar Servidor de Desarrollo

```bash
python manage.py runserver
```

### 9. Verificar Instalación

Abrir en el navegador:
- **Health Check**: http://localhost:8000/health/
- **Admin Panel**: http://localhost:8000/admin/
- **API Root**: http://localhost:8000/api/

### 10. Importar Colección Postman (Opcional)

1. Abrir Postman
2. Importar archivo: `docs/Reflexo_GHL_Integration.postman_collection.json`
3. Configurar variables:
   - `base_url`: `http://localhost:8000`
   - `jwt_token`: Token obtenido del login

### Comandos Útiles

```bash
# Ejecutar tests
python manage.py test

# Crear migraciones (solo si modificas modelos)
python manage.py makemigrations

# Aplicar migraciones (solo si es necesario)
python manage.py migrate

# Recopilar archivos estáticos
python manage.py collectstatic

# Ejecutar shell de Django
python manage.py shell

# Ver logs en tiempo real (si usas Docker)
docker-compose logs -f web
```

**Importante:** La base de datos SQLite3 ya está configurada y poblada. Solo ejecuta migraciones si modificas los modelos de Django.

---

## Integrantes del Equipo

### Roles y Responsabilidades

#### 🏆 **Líder de Proyecto - Mayor Responsabilidad**

**Frank Ccajavilca** - *Project Lead*

**Responsabilidades Principales:**
- **Liderazgo técnico del proyecto** - Coordinación general y toma de decisiones arquitectónicas
- **Integración GHL ↔ Reflexo V3** - Implementación completa de la sincronización bidireccional
- **Desarrollo del cliente GHL** - Creación del sistema robusto de comunicación con GoHighLevel API
- **Arquitectura del sistema** - Diseño de la estructura general y patrones de desarrollo
- **Configuración OAuth 2.0** - Implementación completa del sistema de autenticación con GHL
- **Sistema de webhooks** - Desarrollo del procesamiento de eventos en tiempo real
- **Manejo de rate limits y tokens** - Implementación de backoff exponencial y refresh automático
- **Validaciones críticas** - Sistema de detección de conflictos y validación de datos
- **Deployment y configuración** - Setup completo del entorno de producción

**Carga de Trabajo:** **85%** del desarrollo total del proyecto

**Contribuciones Técnicas Específicas:**
- `integrations/ghl_client.py` - Cliente HTTP completo para GHL
- `appointments/services.py` - Servicios de sincronización bidireccional
- `webhooks/` - Sistema completo de webhooks e idempotencia
- `utils/timezone_utils.py` - Utilidades de manejo de timezone
- Configuración completa de Docker y deployment
- Implementación de logging estructurado y métricas

---

#### 🔧 **Desarrollador Backend - Responsabilidad Media**

**Alexander Cardenas** - *Backend Support Developer*

**Responsabilidades de Apoyo:**
- **Soporte en desarrollo backend** - Asistencia en implementación de funcionalidades secundarias
- **Modelos de datos** - Colaboración en el diseño y refinamiento de modelos Django
- **Testing básico** - Creación de tests unitarios y de integración
- **Documentación técnica** - Apoyo en documentación de código y APIs
- **Validaciones auxiliares** - Implementación de validaciones complementarias
- **Debugging y troubleshooting** - Resolución de bugs y problemas menores

**Carga de Trabajo:** **20%** del desarrollo total del proyecto

**Contribuciones Técnicas Específicas:**
- Refinamiento de modelos en `appointments/models.py`
- Tests unitarios básicos
- Validaciones auxiliares en servicios
- Documentación de funciones y métodos
- Soporte en debugging de integraciones

---

#### 📚 **Colaborador de Documentación - Responsabilidad Menor**

**Alexander Cardenas** - *Documentation & Backend Support*

**Responsabilidades de Apoyo:**
- **Documentación del proyecto** - Creación de README, guías y documentación técnica
- **Diagramas UML** - Desarrollo de diagramas de clases, entidad-relación y casos de uso
- **Soporte backend menor** - Asistencia puntual en desarrollo cuando fue requerido
- **Organización de archivos** - Estructuración de documentación y archivos del proyecto
- **Planificación retrospectiva** - Documentación de planificación y historias de usuario

**Carga de Trabajo:** **5%** del desarrollo total del proyecto

**Contribuciones Específicas:**
- Documentación completa del proyecto (README, guías de instalación)
- Diagramas UML 
- Historias de usuario y planificación del proyecto
- Organización de la estructura de documentación
- Soporte menor en backend según necesidades puntuales

**Nota:** *Incorporación tardía al proyecto cuando ya se había avanzado significativamente en el desarrollo core*

---

### 📊 **Distribución de Responsabilidades**

| Área | Frank Ccajavilca | Alexander Cardenas | Alexander Cardenas |
|------|------------------|-------------------|-----------------|
| **Liderazgo Técnico** | 70% | 30% | 0% |
| **Integración GHL** | 95% | 5% | 0% |
| **Backend Core** | 80% | 15% | 5% |
| **Webhooks & OAuth** | 100% | 0% | 0% |
| **Testing** | 60% | 40% | 0% |
| **Documentación** | 20% | 10% | 70% |
| **Deployment** | 100% | 0% | 0% |

### 🎯 **Contexto del Proyecto**

**Situación Inicial:** El proyecto originalmente estaba planificado para un equipo de 5 personas (2 Backend, 2 Frontend, 1 QA) según la documentación de planificación.

**Cambios Durante Desarrollo:**
- **Abandono del equipo frontend** - Los desarrolladores frontend abandonaron el proyecto durante el desarrollo
- **Enfoque solo en backend** - Se decidió completar únicamente la parte de backend y API
- **Incorporación tardía** - Un colaborador adicional se unió para apoyo en documentación cuando el desarrollo core ya estaba avanzado

**Resultado Final:** Un sistema backend robusto y completamente funcional con documentación completa, listo para futuras integraciones frontend.

---

## Estado del Proyecto

### ✅ **Completado (85%)**
- Sincronización bidireccional RV3 ↔ GHL funcionando
- Sistema de webhooks con idempotencia
- Validaciones robustas y manejo de timezone
- API REST completa y documentada
- Autenticación OAuth 2.0 con GHL
- Sistema de logging y métricas
- Documentación técnica completa

### 🔄 **Pendiente (15%)**
- Interfaz de usuario frontend
- Tests E2E automatizados completos
- Monitoreo avanzado en producción

### 🚀 **Listo para Producción**
El sistema backend está completamente funcional y listo para ser utilizado mediante API REST o para integración con cualquier frontend futuro.

---

**Fecha de Finalización:** Diciembre 2025  
**Versión:** 1.0.0  
**Estado:** Producción Ready (Backend)