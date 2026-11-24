
from django.db import models


# ==========================================
# 1. MESURES DU CAPTEUR DHT11
# ==========================================

class Dht11(models.Model):
    temp = models.FloatField(null=True)
    hum = models.FloatField(null=True)
    dt = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return f"{self.temp} °C - {self.dt}"


# ==========================================
# 2. OPERATEURS
# ==========================================

class Operator(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telegram_chat_id = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


# ==========================================
# 3. INCIDENTS
# ==========================================

class Incident(models.Model):

    STATUS_CHOICES = [
        ('ACTIVE', 'En cours'),
        ('CLOSED', 'Terminé'),
    ]

    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    start_temperature = models.FloatField()
    max_temperature = models.FloatField()
    end_temperature = models.FloatField(null=True, blank=True)

    # Nombre total d'alertes envoyées
    alert_count = models.PositiveIntegerField(default=0)

    # Date et heure du prochain rappel
    next_alert_at = models.DateTimeField(null=True, blank=True)

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='ACTIVE'
    )

    def __str__(self):
        return f"Incident #{self.id} - {self.status}"


# ==========================================
# 4. HISTORIQUE DES ALERTES
# ==========================================

class IncidentAlert(models.Model):

    incident = models.ForeignKey(
        Incident,
        on_delete=models.CASCADE,
        related_name='alerts'
    )

    counter = models.PositiveIntegerField()
    temperature = models.FloatField()
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Incident #{self.incident.id} - Alerte {self.counter}"


# ==========================================
# 5. ENVOIS AUX OPERATEURS
# ==========================================

class AlertDelivery(models.Model):

    alert = models.ForeignKey(
        IncidentAlert,
        on_delete=models.CASCADE,
        related_name='deliveries'
    )

    operator = models.ForeignKey(
        Operator,
        on_delete=models.PROTECT,
        related_name='alert_deliveries'
    )

    email_sent = models.BooleanField(default=False)
    telegram_sent = models.BooleanField(default=False)

    error_message = models.TextField(blank=True)

    # Confirmation de réception
    acknowledged_at = models.DateTimeField(
        null=True,
        blank=True
    )

    # Message écrit par l'opérateur
    operator_message = models.TextField(blank=True)

    def __str__(self):
        return f"{self.operator.name} - Alerte #{self.alert.counter}"


# ==========================================
# 6. REPONSES DES OPERATEURS
# ==========================================

class OperatorResponse(models.Model):

    RESPONSE_CHOICES = [
        ('ACKNOWLEDGED', 'A reçu l’alerte'),
        ('RESOLVED', 'A déclaré l’incident résolu'),
    ]

    incident = models.ForeignKey(
        Incident,
        on_delete=models.CASCADE,
        related_name='responses'
    )

    operator = models.ForeignKey(
        Operator,
        on_delete=models.PROTECT,
        related_name='responses'
    )

    response = models.CharField(
        max_length=20,
        choices=RESPONSE_CHOICES
    )

    responded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.operator.name} - {self.response}"
