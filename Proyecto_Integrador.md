Proyecto Integrador Calendarios RV3 ↔ GHL — Sprint del 11 al 17 de noviembre de 2025 (SALA 1)
Alcance y meta de la célula
Objetivo: entregar sincronización bidireccional estable RV3 ↔ GHL (sUB CUENTA DE REFLEXOPERU) (crear/leer/actualizar/cancelar citas) con TZ correcta y calendarId dinámico.


Tamaño: 5 personas (BK x2, FN x2, QA x1) — con pairing rotativo.


Definición de listo (DoD): flujo E2E verificado, idempotencia de webhooks, errores controlados (401/403/429/5xx), documentación y colección de pruebas listas.


Requisitos: 
Acceso como usuario en https://rv3.marketingmedico.vip/
Acceso a la github una rama frontend de rv3
Credenciales de madrigal


👥 Configuración del equipo (RACI práctico)
BK1 (Líder técnico): arquitectura, endpoints DRF, servicio GHL client, webhooks, idempotencia.


BK2: modelo Cita, migraciones, repositorios, utilidades TZ, pruebas de integración.


FN1: UI de agenda mínima + selector de calendario (calendarId por subcuenta/location).


FN2: vistas de cita (crear/editar), feedback de errores, validaciones de horario.


QA: escenarios E2E, casos borde TZ/overlap, colección Postman, test data.


Reglas breves: WIP ≤ 2 por persona; code review obligatorio; pruebas automáticas mínimas por PR (BK & FN).

🧭 Roadmap por Etapas (modular y secuencial)
Etapa 1 — Base RV3 lista para sincronizar
Resultado: modelo real Cita y API local consistente.
Modelo Cita (campos sugeridos): ghl_appointment_id, ghl_calendar_id, title, contact_id, assigned_user_id, start_time, end_time, status, notes, source, created_at, updated_at.


DRF: POST /api/citas/ (crear), GET /api/citas/?desde&hasta&estado&calendar_id.


TZ: proyecto con USE_TZ=True, America/Lima; helpers para normalizar/mostrar.


Prueba: crear cita local → persiste correcto (tz-aware).


Etapa 2 — Outbound RV3 → GHL
Resultado: crear/actualizar cita en RV3 impacta GHL.
Servicio ghl_client (HTTPX/requests) con: create_appointment, update_appointment, cancel_appointment.


Manejo de tokens y backoff ante 429/5xx; refresco en 401/403.


Guardar ghl_appointment_id de respuesta en la Cita.


Prueba: crear en RV3 → visible en GHL (calendario elegido).


Etapa 3 — Inbound GHL → RV3 (webhooks)
Resultado: mover/cancelar en GHL actualiza RV3 automáticamente.
Endpoint POST /api/webhooks/ghl/appointments/.


Validación de firma (seguridad), parsing de AppointmentCreate/Update/Delete.


Idempotencia: deduplicar por webhookId y/o ghl_appointment_id (tabla eventos o Redis).


Upsert por ghl_appointment_id; Delete → status='canceled' (o soft delete).


Prueba: mover/cancelar desde GHL → cambio reflejado en RV3.


Etapa 4 — CalendarId dinámico y UX mínima
Resultado: calendarId seleccionable por subcuenta y persistido.
Endpoint GET /api/ghl/calendars/ para listar.


UI (React): selector de calendario + persistencia (ej. LocationSettings).


Prueba: cambiar calendarId en UI y repetir E2E.


Etapa 5 — Estabilidad operacional
Resultado: operación robusta en ráfaga y con errores reales.
Logs de cabeceras de límite (X-RateLimit-*) y métrica simple (requests ok/fail).


Reintentos exponenciales con jitter; colas ligeras para re-procesos (si aplica).


Overlaps: validación de solapes/ocupados; reglas simples de conflicto.


Prueba: ráfaga de 10–20 citas y simulación de 429/5xx.


Etapa 6 — Cierre E2E + documentación y demo
Resultado: entregable demostrable y mantenible.
Colección Postman: crear/listar/actualizar/cancelar + webhook mock.


README (instalación, .env, rutas, flujos de ejemplo, códigos de error).


Video corto (2–3 min): ida y vuelta completo.


Checklist de aceptación y matriz de riesgos.



📦 Backlog mínimo por rol (para cargar al tablero)
Backend
[BK] Modelo Cita + migraciones + serializer.


[BK] Endpoints POST/GET /api/citas/.


[BK] Utilidades TZ (to_lima, validación cruce medianoche).


[BK] ghl_client (create/update/cancel + refresh + backoff).


[BK] Webhook appointments + validación firma + idempotencia.


[BK] GET /api/ghl/calendars/ (discovery).


[BK] Persistencia de calendar_id por subcuenta/location (tabla LocationSettings).


Frontend
[FN] UI mínima de agenda (lista/crear/editar).


[FN] Selector de calendario (leer/guardar).


[FN] Manejo de errores (401/403/429) y mensajes claros.


[FN] Validaciones de horarios (no negativos, start<end, TZ vista usuario).


QA
[QA] Casos E2E (crear, mover, cancelar, reintentos).


[QA] Casos borde TZ (23:30→00:30, cambio de día).


[QA] Ráfaga y 429; reenvío de webhooks duplicados.


[QA] Colección Postman y data set de prueba.



🧱 Arquitectura y patrones recomendados
Wrapper HTTP (ghl_client) con decorador @with_token_refresh_and_backoff.


Idempotencia fuerte en webhooks: transacción + select_for_update().


Separación de capas: serializadores/servicios/repositorios (no lógica en views).


Feature flag para alternar “mock vs real” (útil durante el hardening).


Observabilidad ligera: logs estructurados + contador de errores/réplicas.



⚠️ Riesgos técnicos y mitigación
TZ incorrecta → utilidades centralizadas y pruebas con horarios borde.


Doble procesamiento de webhooks → deduplicación + transacciones.


Rate limit → backoff y colas; registrar X-RateLimit-Remaining.


Modelo Cita corto → añadir extras (JSONField) para futuras extensiones.


Tokens expirados → refresco automático + alarmas mínimas en logs.



✅ Criterios de aceptación (demo final)
RV3 → GHL: crear/editar/cancelar en RV3 se refleja en GHL con el calendarId seleccionado.


GHL → RV3: mover/cancelar en GHL llega por webhook y actualiza la misma Cita por ghl_appointment_id.


TZ: todas las fechas persisten y se muestran en America/Lima sin desfaces.


Estabilidad: ráfagas manejadas sin 429 visibles al usuario (solo backoff internamente).


Docs/Pruebas: README + Postman + video de 2–3 min listos.



📊 Métricas mínimas de salida
Tiempo medio de alta de cita (RV3→GHL).


% de webhooks procesados a la primera (sin reintento).


Errores por tipo (401/403/429/5xx) por 100 operaciones.


Cobertura básica (tests BK/FN críticos).



📝 Entregables
Código RV3 (BK & FN) + colección Postman.


README operativo y de arquitectura.


Video demo E2E.


Checklist de aceptación firmado por PO.



🎓 Preguntas de evaluación técnica (para certificación individual)
¿Cómo garantizas idempotencia al procesar AppointmentUpdate y AppointmentDelete? Explica el flujo y la estructura de datos que usas.


¿Qué diferencias prácticas hay entre hora naive y hora aware en Django? ¿Cómo asegurar que todo opere en America/Lima de punta a punta?


Detalla el mapping mínimo de campos entre Cita (RV3) y un Appointment de GHL para crear y para actualizar.


¿Cómo implementarías backoff exponencial con jitter ante 429/5xx y cómo registrarías X-RateLimit-* para observabilidad?


¿Qué harías si recibes un webhook con firma inválida o con payload incompleto? Describe la política de seguridad y logging.


Explica el flujo de refresh de token ante 401/403 y cómo evitar condiciones de carrera cuando múltiples hilos lo intentan a la vez.


¿Cómo resolverías el calendarId dinámico por subcuenta/location y qué cambios harías si mañana hay múltiples calendarios por médico/sala?


¿Qué validaciones de negocio/horario aplicarías al crear una cita para evitar solapes y datos inconsistentes (start/end, duración mínima, etc.)?


Diseña una prueba E2E que valide: crear en RV3, mover en GHL, cancelar en GHL; incluye aserciones de DB y respuestas HTTP.


¿Qué estrategia usarías para reprocesar webhooks fallidos sin duplicar efectos y cómo demostrarías que tu pipeline es a prueba de duplicados?

