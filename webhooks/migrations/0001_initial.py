# Generated manually for webhooks app

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='WebhookEvent',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('webhook_id', models.CharField(help_text='ID único del webhook (puede ser generado o enviado por GHL)', max_length=255, unique=True)),
                ('event_type', models.CharField(help_text='Tipo de evento: AppointmentCreate, AppointmentUpdate, AppointmentDelete', max_length=100)),
                ('ghl_appointment_id', models.CharField(help_text='ID de la cita en GHL', max_length=255)),
                ('processed_at', models.DateTimeField(auto_now_add=True, help_text='Timestamp de cuando se procesó el evento')),
                ('payload_hash', models.CharField(help_text='SHA256 hash del payload para detectar duplicados exactos', max_length=64)),
                ('success', models.BooleanField(default=True, help_text='Si el procesamiento fue exitoso')),
                ('error_message', models.TextField(blank=True, help_text='Mensaje de error si el procesamiento falló')),
            ],
            options={
                'verbose_name': 'Evento de Webhook',
                'verbose_name_plural': 'Eventos de Webhook',
                'db_table': 'webhook_events',
                'ordering': ['-processed_at'],
            },
        ),
        migrations.AddIndex(
            model_name='webhookevent',
            index=models.Index(fields=['webhook_id'], name='webhook_eve_webhook_b7c89e_idx'),
        ),
        migrations.AddIndex(
            model_name='webhookevent',
            index=models.Index(fields=['ghl_appointment_id', 'event_type'], name='webhook_eve_ghl_app_4c8a9f_idx'),
        ),
        migrations.AddIndex(
            model_name='webhookevent',
            index=models.Index(fields=['processed_at'], name='webhook_eve_process_8f2b1d_idx'),
        ),
        migrations.AddIndex(
            model_name='webhookevent',
            index=models.Index(fields=['payload_hash'], name='webhook_eve_payload_3e7c2a_idx'),
        ),
    ]