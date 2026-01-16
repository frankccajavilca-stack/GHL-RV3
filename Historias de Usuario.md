# 📋 Historias de Usuario - Proyecto Integrador RV3 ↔ GHL

## 📊 Información del Proyecto

**Proyecto**: Integración Calendarios RV3 ↔ GoHighLevel  
**Sprint**: 14-22 diciembre 2025  
**Equipo**: 5 personas (BK x2, FN x2, QA x1)

---

## 🎯 Épicas del Proyecto

### **Épica 1**: Sincronización RV3 → GHL
### **Épica 2**: Sincronización GHL → RV3  
### **Épica 3**: Gestión de Calendarios
### **Épica 4**: Robustez y Estabilidad
### **Épica 5**: Interfaz de Usuario
### **Épica 6**: Testing y Documentación

---

## 📝 Historias de Usuario por Épica

### **🔄 Épica 1: Sincronización RV3 → GHL**

#### **HU-001: Crear Cita en RV3**
**Como** administrador de la clínica  
**Quiero** crear una cita en RV3  
**Para que** aparezca automáticamente en GoHighLevel

**Criterios de Aceptación:**
- ✅ Al crear una cita en RV3, se genera automáticamente en GHL
- ✅ Todos los campos se mapean correctamente (título, horario, contacto)
- ✅ Se guarda el ID de GHL en la cita de RV3
- ✅ El proceso toma menos de 3 segundos
- ✅ Se muestra confirmación de sincronización exitosa

**Prioridad**: Alta  
**Estimación**: 8 puntos  
**Responsable**: BK1

---

#### **HU-002: Actualizar Cita en RV3**
**Como** recepcionista  
**Quiero** modificar una cita existente en RV3  
**Para que** los cambios se reflejen automáticamente en GHL

**Criterios de Aceptación:**
- ✅ Al editar horario, título o notas en RV3, se actualiza en GHL
- ✅ Los cambios se sincronizan en tiempo real
- ✅ Se mantiene la integridad de los datos
- ✅ Se registra el historial de cambios
- ✅ Se maneja correctamente si la cita no existe en GHL

**Prioridad**: Alta  
**Estimación**: 5 puntos  
**Responsable**: BK1

---

#### **HU-003: Cancelar Cita en RV3**
**Como** administrador  
**Quiero** cancelar una cita en RV3  
**Para que** el estado se actualice automáticamente en GHL

**Criterios de Aceptación:**
- ✅ Al cancelar en RV3, el estado cambia a "cancelada" en GHL
- ✅ Se preserva la información de la cita cancelada
- ✅ Se notifica la cancelación exitosa
- ✅ No se permite reactivar citas canceladas
- ✅ Se maneja el caso de citas ya canceladas

**Prioridad**: Media  
**Estimación**: 3 puntos  
**Responsable**: BK2

---

### **🔄 Épica 2: Sincronización GHL → RV3**

#### **HU-004: Recibir Cita Creada desde GHL**
**Como** sistema RV3  
**Quiero** recibir notificación cuando se crea una cita en GHL  
**Para que** aparezca automáticamente en RV3

**Criterios de Aceptación:**
- ✅ Webhook de GHL se procesa correctamente
- ✅ Nueva cita aparece en RV3 con source="ghl"
- ✅ Todos los campos se mapean correctamente
- ✅ Se evitan duplicados si el webhook se envía múltiples veces
- ✅ Se valida la autenticidad del webhook

**Prioridad**: Alta  
**Estimación**: 8 puntos  
**Responsable**: BK1

---

#### **HU-005: Actualizar Cita desde GHL**
**Como** sistema RV3  
**Quiero** recibir actualizaciones de citas modificadas en GHL  
**Para que** los cambios se reflejen en RV3

**Criterios de Aceptación:**
- ✅ Cambios de horario en GHL se actualizan en RV3
- ✅ Modificaciones de título y notas se sincronizan
- ✅ Se identifica la cita correcta por ghl_appointment_id
- ✅ Se crea la cita si no existe en RV3 (upsert)
- ✅ Se mantiene la integridad de datos locales

**Prioridad**: Alta  
**Estimación**: 6 puntos  
**Responsable**: BK1

---

#### **HU-006: Cancelar Cita desde GHL**
**Como** sistema RV3  
**Quiero** recibir notificación de citas canceladas en GHL  
**Para que** el estado se actualice en RV3

**Criterios de Aceptación:**
- ✅ Cita cancelada en GHL se marca como cancelada en RV3
- ✅ Se preserva la información histórica
- ✅ Se actualiza el estado sin eliminar el registro
- ✅ Se maneja el caso de citas ya canceladas
- ✅ Se procesa correctamente aunque la cita no exista

**Prioridad**: Media  
**Estimación**: 4 puntos  
**Responsable**: BK2

---

### **📅 Épica 3: Gestión de Calendarios**

#### **HU-007: Listar Calendarios Disponibles**
**Como** administrador  
**Quiero** ver todos los calendarios disponibles en GHL  
**Para** seleccionar en cuál crear las citas

**Criterios de Aceptación:**
- ✅ Se muestran todos los calendarios activos de la subcuenta
- ✅ Se incluye nombre, ID y descripción de cada calendario
- ✅ La lista se actualiza dinámicamente desde GHL
- ✅ Se maneja el caso de calendarios inactivos
- ✅ Se muestra estado de conexión con GHL

**Prioridad**: Alta  
**Estimación**: 5 puntos  
**Responsable**: BK1

---

#### **HU-008: Seleccionar Calendario por Defecto**
**Como** administrador de subcuenta  
**Quiero** configurar un calendario por defecto  
**Para que** las nuevas citas se creen automáticamente ahí

**Criterios de Aceptación:**
- ✅ Puedo seleccionar un calendario de la lista disponible
- ✅ La configuración se guarda por subcuenta/location
- ✅ Todas las nuevas citas usan el calendario seleccionado
- ✅ Puedo cambiar el calendario por defecto en cualquier momento
- ✅ Se valida que el calendario seleccionado esté activo

**Prioridad**: Alta  
**Estimación**: 4 puntos  
**Responsable**: FN1

---

#### **HU-009: Cambiar Calendario de Cita**
**Como** recepcionista  
**Quiero** poder cambiar el calendario de una cita específica  
**Para** organizarlas según el tipo de consulta

**Criterios de Aceptación:**
- ✅ Puedo seleccionar un calendario diferente al crear la cita
- ✅ Puedo cambiar el calendario de una cita existente
- ✅ El cambio se sincroniza automáticamente con GHL
- ✅ Se valida que el calendario destino esté disponible
- ✅ Se mantiene el historial de cambios

**Prioridad**: Media  
**Estimación**: 6 puntos  
**Responsable**: FN1

---

### **🛡️ Épica 4: Robustez y Estabilidad**

#### **HU-010: Manejar Rate Limits de GHL**
**Como** sistema  
**Quiero** manejar automáticamente los límites de velocidad de GHL  
**Para** evitar errores y bloqueos del servicio

**Criterios de Aceptación:**
- ✅ Se detectan automáticamente los errores 429 (rate limit)
- ✅ Se implementa backoff exponencial con jitter
- ✅ Se reintenta automáticamente después del tiempo de espera
- ✅ Se registran las métricas de rate limit
- ✅ El usuario no ve errores durante el backoff

**Prioridad**: Alta  
**Estimación**: 6 puntos  
**Responsable**: BK1

---

#### **HU-011: Renovar Tokens Automáticamente**
**Como** sistema  
**Quiero** renovar automáticamente los tokens de GHL  
**Para** mantener la conectividad sin intervención manual

**Criterios de Aceptación:**
- ✅ Se detectan automáticamente los errores 401/403
- ✅ Se renueva el token usando el refresh token
- ✅ Se reintenta la operación original tras renovar
- ✅ Se registra en logs cuando se renueva un token
- ✅ Se alerta si no se puede renovar el token

**Prioridad**: Alta  
**Estimación**: 5 puntos  
**Responsable**: BK1

---

#### **HU-012: Validar Conflictos de Horario**
**Como** recepcionista  
**Quiero** que el sistema detecte conflictos de horario  
**Para** evitar citas superpuestas

**Criterios de Aceptación:**
- ✅ Se valida que no haya overlaps al crear una cita
- ✅ Se muestra mensaje claro si hay conflicto
- ✅ Se sugieren horarios alternativos disponibles
- ✅ Se valida tanto en RV3 como en GHL
- ✅ Se considera el calendario específico para la validación

**Prioridad**: Media  
**Estimación**: 7 puntos  
**Responsable**: BK2

---

#### **HU-013: Manejar Timezone Correctamente**
**Como** usuario del sistema  
**Quiero** que todas las horas se muestren en hora de Lima  
**Para** evitar confusiones de horario

**Criterios de Aceptación:**
- ✅ Todas las fechas se almacenan en UTC en la base de datos
- ✅ Todas las fechas se muestran en America/Lima en la UI
- ✅ Las conversiones son correctas en casos borde (23:30→00:30)
- ✅ Los cambios de día se manejan correctamente
- ✅ La sincronización con GHL mantiene la hora correcta

**Prioridad**: Alta  
**Estimación**: 8 puntos  
**Responsable**: BK2

---

### **🎨 Épica 5: Interfaz de Usuario**

#### **HU-014: Ver Lista de Citas**
**Como** recepcionista  
**Quiero** ver una lista de todas las citas  
**Para** tener una vista general de la agenda

**Criterios de Aceptación:**
- ✅ Se muestran las citas ordenadas por fecha y hora
- ✅ Se incluye título, paciente, horario y estado
- ✅ Se puede filtrar por fecha, estado y calendario
- ✅ Se actualiza automáticamente cuando hay cambios
- ✅ Se indica el origen de cada cita (RV3 o GHL)

**Prioridad**: Alta  
**Estimación**: 5 puntos  
**Responsable**: FN1

---

#### **HU-015: Crear Cita desde UI**
**Como** recepcionista  
**Quiero** crear una nueva cita desde la interfaz  
**Para** agendar pacientes fácilmente

**Criterios de Aceptación:**
- ✅ Formulario con todos los campos necesarios
- ✅ Validación en tiempo real de horarios
- ✅ Selector de calendario disponible
- ✅ Validación de conflictos antes de guardar
- ✅ Confirmación visual de creación exitosa

**Prioridad**: Alta  
**Estimación**: 6 puntos  
**Responsable**: FN2

---

#### **HU-016: Editar Cita desde UI**
**Como** recepcionista  
**Quiero** modificar una cita existente  
**Para** actualizar información o cambiar horarios

**Criterios de Aceptación:**
- ✅ Formulario pre-llenado con datos actuales
- ✅ Validación de nuevos horarios
- ✅ Posibilidad de cambiar calendario
- ✅ Confirmación antes de guardar cambios
- ✅ Indicación visual de sincronización con GHL

**Prioridad**: Media  
**Estimación**: 5 puntos  
**Responsable**: FN2

---

#### **HU-017: Manejar Errores en UI**
**Como** usuario  
**Quiero** recibir mensajes claros cuando hay errores  
**Para** entender qué pasó y cómo solucionarlo

**Criterios de Aceptación:**
- ✅ Mensajes de error claros y en español
- ✅ Diferenciación entre errores temporales y permanentes
- ✅ Botón de reintentar para errores temporales
- ✅ Indicación de estado de conexión con GHL
- ✅ Guías de solución para errores comunes

**Prioridad**: Media  
**Estimación**: 4 puntos  
**Responsable**: FN2

---

### **🧪 Épica 6: Testing y Documentación**

#### **HU-018: Probar Flujo E2E**
**Como** QA  
**Quiero** validar el flujo completo de sincronización  
**Para** asegurar que todo funciona correctamente

**Criterios de Aceptación:**
- ✅ Crear cita en RV3 → aparece en GHL
- ✅ Modificar cita en GHL → se actualiza en RV3
- ✅ Cancelar cita en cualquier sistema → se sincroniza
- ✅ Cambiar calendario → afecta nuevas citas
- ✅ Manejar errores y reconexión automática

**Prioridad**: Alta  
**Estimación**: 8 puntos  
**Responsable**: QA

---

#### **HU-019: Validar Idempotencia**
**Como** QA  
**Quiero** probar que los webhooks duplicados no causen problemas  
**Para** asegurar la integridad de los datos

**Criterios de Aceptación:**
- ✅ Enviar el mismo webhook múltiples veces
- ✅ Verificar que solo se procesa una vez
- ✅ Confirmar que no hay duplicados en la base de datos
- ✅ Probar con diferentes tipos de eventos
- ✅ Validar bajo condiciones de alta concurrencia

**Prioridad**: Alta  
**Estimación**: 6 puntos  
**Responsable**: QA

---

#### **HU-020: Documentar API**
**Como** desarrollador  
**Quiero** tener documentación completa de la API  
**Para** poder integrarme fácilmente

**Criterios de Aceptación:**
- ✅ Colección Postman con todos los endpoints
- ✅ Ejemplos de request y response para cada endpoint
- ✅ Documentación de códigos de error
- ✅ Guía de autenticación y configuración
- ✅ Tests automatizados en Postman

**Prioridad**: Media  
**Estimación**: 4 puntos  
**Responsable**: QA

---

#### **HU-021: Crear Guía de Instalación**
**Como** administrador de sistemas  
**Quiero** una guía clara de instalación  
**Para** poder desplegar el sistema correctamente

**Criterios de Aceptación:**
- ✅ Instrucciones paso a paso de instalación
- ✅ Configuración de variables de entorno
- ✅ Guía de configuración de GHL
- ✅ Troubleshooting de problemas comunes
- ✅ Video demo del funcionamiento

**Prioridad**: Media  
**Estimación**: 3 puntos  
**Responsable**: FN2

---

## 📊 Resumen de Historias

### **Por Prioridad**
- **Alta**: 12 historias (HU-001, 002, 004, 005, 007, 008, 010, 011, 013, 014, 015, 018, 019)
- **Media**: 9 historias (HU-003, 006, 009, 012, 016, 017, 020, 021)

### **Por Responsable**
- **BK1**: 7 historias (HU-001, 002, 004, 005, 007, 010, 011)
- **BK2**: 4 historias (HU-003, 006, 012, 013)
- **FN1**: 3 historias (HU-008, 009, 014)
- **FN2**: 4 historias (HU-015, 016, 017, 021)
- **QA**: 3 historias (HU-018, 019, 020)

### **Estimación Total**
- **Total de puntos**: 118 puntos
- **Promedio por historia**: 5.6 puntos
- **Distribución por sprint**: ~13 puntos por día

---

## 📋 Criterios de Aceptación Generales

### **Definición de Terminado (DoD)**
Para que una historia se considere terminada debe cumplir:

- ✅ **Funcionalidad**: Cumple todos los criterios de aceptación
- ✅ **Testing**: Tiene tests automatizados que pasan
- ✅ **Code Review**: Ha sido revisada y aprobada
- ✅ **Documentación**: Está documentada en Postman/README
- ✅ **Demo**: Funciona en demo con datos reales

### **Criterios de Calidad**
- ✅ **Performance**: Respuesta < 3 segundos
- ✅ **Reliability**: 95% de operaciones exitosas
- ✅ **Usability**: Mensajes de error claros
- ✅ **Security**: Validación de webhooks y tokens
- ✅ **Maintainability**: Código limpio y documentado

---

**Documento creado**: 14 de diciembre de 2025  
**Última actualización**: 14 de diciembre de 2025  
**Responsable**: Product Owner GHL-RV3