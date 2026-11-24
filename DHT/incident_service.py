
from django.utils import timezone

from .models import Incident
from .alert_service import traiter_alerte


# ==========================================
# CONFIGURATION
# ==========================================

SEUIL_TEMPERATURE = 20


# ==========================================
# TRAITER UNE MESURE DU CAPTEUR
# ==========================================

def traiter_mesure(mesure):

    temperature = mesure.temp

    incident = Incident.objects.filter(
        status='ACTIVE'
    ).order_by('-started_at').first()

    # ======================================
    # 1. TEMPERATURE NORMALE : <= 25 °C
    # ======================================

    if temperature is None or temperature <= SEUIL_TEMPERATURE:

        if incident:

            incident.status = 'CLOSED'
            incident.ended_at = mesure.dt or timezone.now()
            incident.end_temperature = temperature
            incident.next_alert_at = None

            incident.save(update_fields=[
                'status',
                'ended_at',
                'end_temperature',
                'next_alert_at'
            ])

        return None

    # ======================================
    # 2. CREER UN NOUVEL INCIDENT
    # ======================================

    if incident is None:

        incident = Incident.objects.create(
            start_temperature=temperature,
            max_temperature=temperature,
            alert_count=0,
            status='ACTIVE'
        )

        # Envoyer immédiatement la première alerte
        traiter_alerte(incident, temperature)

        return incident

    # ======================================
    # 3. METTRE A JOUR L'INCIDENT EXISTANT
    # ======================================

    if temperature > incident.max_temperature:

        incident.max_temperature = temperature

        incident.save(update_fields=[
            'max_temperature'
        ])

    return incident
