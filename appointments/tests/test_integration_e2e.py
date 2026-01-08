"""
Tests de integración E2E para sincronización RV3 ↔ GHL
"""
import os
import django
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

from appointments.models import Cita
from appointments.services import AppointmentSyncService, AppointmentValidationService
from webhooks.handlers import WebhookHandler
from webhooks.models import WebhookEvent
from locations.models import LocationSettings

User = get_user_model()

class GHLIntegrationE2ETestCase(APITestCase):
    """Tests E2E para integración completa RV3 ↔ GHL"""
    
    def setUp(self):
        """Configuración inicial para tests"""
        # Crear usuario de prueba
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Datos de prueba
        self.test_calendar_id = 'test_calendar_123'
        self.test_contact_id = 'test_contact_456'
        self.test_location_id = 'test_location_789'
        
        # Crear location de prueba
        self.location = LocationSettings.objects.create(
            ghl_location_id=self.test_location_id,
            name='Test Location',
            timezone='America/Lima',
            default_calendar_id=self.test_calendar_id,
            is_active=True
        )
        
        # Datos base para citas
        self.base_cita_data = {
            'title': 'Test Cita E2E',
            'contact_id': self.test_contact_id,
            'ghl_calendar_id': self.test_calendar_id,
            'start_time': (timezone.now() + timedelta(days=1)).isoformat(),
            'end_time': (timezone.now() + timedelta(days=1, hours=1)).isoformat(),
            'notes': 'Cita de prueba E2E'
        }
    
    @patch('integrations.ghl_client.ghl_client.create_appointment')
    @patch('integrations.ghl_client.ghl_client.get_calendars')
    def test_e2e_create_appointment_rv3_to_ghl(self, mock_get_calendars, mock_create):
        """
        Test E2E: Crear cita en RV3 → Sincronizar a GHL
        
        Flujo:
        1. Crear cita en RV3 via API
        2. Verificar sincronización automática a GHL
        3. Verificar que se guarda ghl_appointment_id
        """
        # Mock respuestas de GHL
        mock_get_calendars.return_value = {
            'calendars': [
                {
                    'id': self.test_calendar_id,
                    'name': 'Test Calendar',
                    'isActive': True
                }
            ]
        }
        
        mock_create.return_value = {
            'id': 'ghl_appointment_123',
            'status': 'scheduled'
        }
        
        # 1. Crear cita via API
        response = self.client.post('/api/ghl/citas/', self.base_cita_data)
        
        # Verificaciones
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        cita_data = response.json()
        self.assertIsNotNone(cita_data['id'])
        
        # 2. Verificar que se llamó a GHL
        mock_create.assert_called_once()
        
        # 3. Verificar cita en BD
        cita = Cita.objects.get(id=cita_data['id'])
        self.assertEqual(cita.title, self.base_cita_data['title'])
        self.assertEqual(cita.source, 'rv3')
        self.assertIsNotNone(cita.ghl_appointment_id)
    
    @patch('integrations.ghl_client.ghl_client.update_appointment')
    def test_e2e_update_appointment_sync(self, mock_update):
        """
        Test E2E: Actualizar cita en RV3 → Sincronizar a GHL
        """
        # Crear cita inicial
        cita = Cita.objects.create(
            ghl_appointment_id='ghl_123',
            **self.base_cita_data
        )
        
        mock_update.return_value = {'id': 'ghl_123', 'status': 'confirmed'}
        
        # Actualizar via API
        update_data = {
            **self.base_cita_data,
            'title': 'Cita ACTUALIZADA',
            'status': 'confirmed'
        }
        
        response = self.client.put(f'/api/ghl/citas/{cita.id}/', update_data)
        
        # Verificaciones
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_update.assert_called_once_with('ghl_123', unittest.mock.ANY)
        
        # Verificar actualización en BD
        cita.refresh_from_db()
        self.assertEqual(cita.title, 'Cita ACTUALIZADA')
        self.assertEqual(cita.status, 'confirmed')
    
    @patch('integrations.ghl_client.ghl_client.cancel_appointment')
    def test_e2e_cancel_appointment_sync(self, mock_cancel):
        """
        Test E2E: Cancelar cita en RV3 → Sincronizar a GHL
        """
        # Crear cita inicial
        cita = Cita.objects.create(
            ghl_appointment_id='ghl_123',
            **self.base_cita_data
        )
        
        mock_cancel.return_value = True
        
        # Cancelar via API
        response = self.client.post(f'/api/ghl/citas/{cita.id}/cancel/')
        
        # Verificaciones
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_cancel.assert_called_once_with('ghl_123')
        
        # Verificar cancelación en BD
        cita.refresh_from_db()
        self.assertEqual(cita.status, 'cancelled')
    
    def test_e2e_webhook_appointment_create(self):
        """
        Test E2E: Webhook GHL → Crear cita en RV3
        
        Flujo:
        1. Recibir webhook de GHL
        2. Procesar y crear cita en RV3
        3. Verificar idempotencia
        """
        webhook_data = {
            'type': 'AppointmentCreate',
            'locationId': self.test_location_id,
            'webhookId': 'webhook_test_001',
            'data': {
                'id': 'ghl_webhook_appointment_001',
                'calendarId': self.test_calendar_id,
                'contactId': self.test_contact_id,
                'title': 'Cita desde Webhook',
                'startTime': '2025-12-25T14:00:00.000Z',
                'endTime': '2025-12-25T15:00:00.000Z',
                'appointmentStatus': 'scheduled',
                'notes': 'Creada por webhook'
            }
        }
        
        # 1. Enviar webhook
        response = self.client.post('/api/webhooks/ghl/', webhook_data)
        
        # Verificaciones
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 2. Verificar cita creada
        cita = Cita.objects.get(ghl_appointment_id='ghl_webhook_appointment_001')
        self.assertEqual(cita.title, 'Cita desde Webhook')
        self.assertEqual(cita.source, 'ghl')
        
        # 3. Verificar evento registrado
        webhook_event = WebhookEvent.objects.get(webhook_id='webhook_test_001')
        self.assertEqual(webhook_event.event_type, 'AppointmentCreate')
        self.assertTrue(webhook_event.success)
        
        # 4. Probar idempotencia - enviar mismo webhook
        response2 = self.client.post('/api/webhooks/ghl/', webhook_data)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        
        # Verificar que no se duplicó
        citas_count = Cita.objects.filter(ghl_appointment_id='ghl_webhook_appointment_001').count()
        self.assertEqual(citas_count, 1)
    
    def test_e2e_webhook_appointment_update(self):
        """
        Test E2E: Webhook de actualización GHL → RV3
        """
        # Crear cita inicial
        cita = Cita.objects.create(
            ghl_appointment_id='ghl_update_test',
            title='Cita Original',
            **self.base_cita_data
        )
        
        webhook_data = {
            'type': 'AppointmentUpdate',
            'locationId': self.test_location_id,
            'webhookId': 'webhook_update_001',
            'data': {
                'id': 'ghl_update_test',
                'calendarId': self.test_calendar_id,
                'contactId': self.test_contact_id,
                'title': 'Cita ACTUALIZADA por Webhook',
                'startTime': '2025-12-25T15:00:00.000Z',
                'endTime': '2025-12-25T16:00:00.000Z',
                'appointmentStatus': 'confirmed',
                'notes': 'Actualizada por webhook'
            }
        }
        
        # Enviar webhook de actualización
        response = self.client.post('/api/webhooks/ghl/', webhook_data)
        
        # Verificaciones
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar actualización
        cita.refresh_from_db()
        self.assertEqual(cita.title, 'Cita ACTUALIZADA por Webhook')
        self.assertEqual(cita.status, 'confirmed')
    
    def test_e2e_webhook_appointment_delete(self):
        """
        Test E2E: Webhook de eliminación GHL → RV3
        """
        # Crear cita inicial
        cita = Cita.objects.create(
            ghl_appointment_id='ghl_delete_test',
            **self.base_cita_data
        )
        
        webhook_data = {
            'type': 'AppointmentDelete',
            'locationId': self.test_location_id,
            'webhookId': 'webhook_delete_001',
            'data': {
                'id': 'ghl_delete_test'
            }
        }
        
        # Enviar webhook de eliminación
        response = self.client.post('/api/webhooks/ghl/', webhook_data)
        
        # Verificaciones
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar cancelación (soft delete)
        cita.refresh_from_db()
        self.assertEqual(cita.status, 'cancelled')


class ValidationServiceTestCase(TestCase):
    """Tests para servicio de validaciones"""
    
    def setUp(self):
        self.test_calendar_id = 'test_calendar_validation'
        
        # Crear cita existente para tests de overlap
        self.existing_cita = Cita.objects.create(
            title='Cita Existente',
            contact_id='contact_123',
            ghl_calendar_id=self.test_calendar_id,
            start_time=timezone.now() + timedelta(days=1, hours=10),
            end_time=timezone.now() + timedelta(days=1, hours=11),
            status='scheduled'
        )
    
    def test_overlap_detection(self):
        """Test detección de overlaps"""
        # Horario que se solapa
        overlap_start = self.existing_cita.start_time + timedelta(minutes=30)
        overlap_end = self.existing_cita.end_time + timedelta(minutes=30)
        
        has_overlap, overlapping = AppointmentValidationService.check_overlaps(
            overlap_start, overlap_end, self.test_calendar_id
        )
        
        self.assertTrue(has_overlap)
        self.assertEqual(overlapping.count(), 1)
        self.assertEqual(overlapping.first().id, self.existing_cita.id)
    
    def test_no_overlap(self):
        """Test sin overlaps"""
        # Horario que no se solapa
        no_overlap_start = self.existing_cita.end_time + timedelta(hours=1)
        no_overlap_end = no_overlap_start + timedelta(hours=1)
        
        has_overlap, overlapping = AppointmentValidationService.check_overlaps(
            no_overlap_start, no_overlap_end, self.test_calendar_id
        )
        
        self.assertFalse(has_overlap)
        self.assertEqual(overlapping.count(), 0)
    
    def test_business_hours_validation(self):
        """Test validación de horarios de trabajo"""
        # Horario válido (10 AM - 11 AM)
        valid_start = timezone.now().replace(hour=10, minute=0, second=0, microsecond=0)
        valid_end = valid_start + timedelta(hours=1)
        
        # No debe lanzar excepción
        try:
            AppointmentValidationService.validate_business_hours(valid_start, valid_end)
        except Exception:
            self.fail("Validación de horarios de trabajo falló para horario válido")
        
        # Horario inválido (6 AM - 7 AM)
        invalid_start = timezone.now().replace(hour=6, minute=0, second=0, microsecond=0)
        invalid_end = invalid_start + timedelta(hours=1)
        
        with self.assertRaises(Exception):
            AppointmentValidationService.validate_business_hours(invalid_start, invalid_end)
    
    def test_duration_validation(self):
        """Test validación de duración"""
        base_time = timezone.now()
        
        # Duración válida (30 minutos)
        valid_start = base_time
        valid_end = base_time + timedelta(minutes=30)
        
        try:
            AppointmentValidationService.validate_duration(valid_start, valid_end)
        except Exception:
            self.fail("Validación de duración falló para duración válida")
        
        # Duración muy corta (5 minutos)
        short_end = base_time + timedelta(minutes=5)
        
        with self.assertRaises(Exception):
            AppointmentValidationService.validate_duration(base_time, short_end)
        
        # Duración muy larga (10 horas)
        long_end = base_time + timedelta(hours=10)
        
        with self.assertRaises(Exception):
            AppointmentValidationService.validate_duration(base_time, long_end)


class WebhookIdempotencyTestCase(TransactionTestCase):
    """Tests específicos para idempotencia de webhooks"""
    
    def test_duplicate_webhook_prevention(self):
        """Test prevención de webhooks duplicados"""
        webhook_data = {
            'id': 'test_appointment_idempotency',
            'calendarId': 'test_calendar',
            'contactId': 'test_contact',
            'title': 'Test Idempotency',
            'startTime': '2025-12-25T14:00:00.000Z',
            'endTime': '2025-12-25T15:00:00.000Z',
            'appointmentStatus': 'scheduled'
        }
        
        webhook_id = 'idempotency_test_001'
        
        # Procesar webhook primera vez
        result1 = WebhookHandler.handle_appointment_create(webhook_data, webhook_id)
        
        # Verificar cita creada
        self.assertIsNotNone(result1)
        self.assertEqual(result1.ghl_appointment_id, 'test_appointment_idempotency')
        
        # Procesar mismo webhook segunda vez
        result2 = WebhookHandler.handle_appointment_create(webhook_data, webhook_id)
        
        # Debe retornar None (duplicado ignorado)
        self.assertIsNone(result2)
        
        # Verificar que solo existe una cita
        citas_count = Cita.objects.filter(ghl_appointment_id='test_appointment_idempotency').count()
        self.assertEqual(citas_count, 1)
        
        # Verificar evento registrado
        events_count = WebhookEvent.objects.filter(webhook_id=webhook_id).count()
        self.assertEqual(events_count, 1)
    
    def test_race_condition_prevention(self):
        """Test prevención de race conditions con select_for_update"""
        from threading import Thread
        import time
        
        webhook_data = {
            'id': 'race_condition_test',
            'calendarId': 'test_calendar',
            'contactId': 'test_contact',
            'title': 'Race Condition Test',
            'startTime': '2025-12-25T14:00:00.000Z',
            'endTime': '2025-12-25T15:00:00.000Z',
            'appointmentStatus': 'scheduled'
        }
        
        results = []
        
        def process_webhook(webhook_id):
            try:
                result = WebhookHandler.handle_appointment_create(webhook_data, webhook_id)
                results.append(result)
            except Exception as e:
                results.append(e)
        
        # Crear múltiples threads para simular race condition
        threads = []
        for i in range(3):
            thread = Thread(target=process_webhook, args=[f'race_test_{i}'])
            threads.append(thread)
        
        # Iniciar todos los threads
        for thread in threads:
            thread.start()
        
        # Esperar que terminen
        for thread in threads:
            thread.join()
        
        # Verificar que solo se creó una cita
        citas_count = Cita.objects.filter(ghl_appointment_id='race_condition_test').count()
        self.assertEqual(citas_count, 1)
        
        # Verificar que se procesaron todos los eventos
        successful_results = [r for r in results if isinstance(r, Cita)]
        self.assertEqual(len(successful_results), 1)


import unittest

if __name__ == '__main__':
    unittest.main()