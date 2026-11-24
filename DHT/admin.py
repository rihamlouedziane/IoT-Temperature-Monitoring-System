
from django.contrib import admin
from .models import (
    Dht11,
    Operator,
    Incident,
    IncidentAlert,
    AlertDelivery,
    OperatorResponse
)


@admin.register(Dht11)
class Dht11Admin(admin.ModelAdmin):
    list_display = ('id', 'temp', 'hum', 'dt')
    ordering = ('-dt',)


@admin.register(Operator)
class OperatorAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'telegram_chat_id', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'email')


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'status', 'started_at',
        'ended_at', 'start_temperature',
        'max_temperature', 'alert_count'
    )
    list_filter = ('status',)


@admin.register(IncidentAlert)
class IncidentAlertAdmin(admin.ModelAdmin):
    list_display = ('id', 'incident', 'counter', 'temperature', 'sent_at')


@admin.register(AlertDelivery)
class AlertDeliveryAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'alert', 'operator',
        'email_sent', 'telegram_sent'
    )


@admin.register(OperatorResponse)
class OperatorResponseAdmin(admin.ModelAdmin):
    list_display = ('id', 'incident', 'operator', 'response', 'responded_at')
