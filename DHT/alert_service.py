
import logging
import requests

from datetime import timedelta
from urllib.parse import urlencode

from django.conf import settings
from django.core import signing
from django.core.mail import send_mail
from django.utils import timezone
from django.urls import reverse

from .models import (
    Operator,
    Incident,
    IncidentAlert,
    AlertDelivery,
    Dht11
)

logger = logging.getLogger(__name__)

# ==========================================
# 1. CONFIGURATION
# ==========================================

INTERVALLE_ALERTE = 20  # minutes


# ==========================================
# 2. CREER LE LIEN DE REPONSE
# ==========================================

def creer_lien_reponse(delivery):

    token = signing.dumps(
        {"delivery_id": delivery.id},
        salt="operator-alert-response"
    )

    chemin = reverse("repondre_alerte")
    query = urlencode({"token": token})

    return f"{settings.PUBLIC_BASE_URL.rstrip('/')}{chemin}?{query}"


# ==========================================
# 3. CHOISIR LES OPERATEURS
# ==========================================

def obtenir_destinataires(compteur):

    operateurs = Operator.objects.filter(
        is_active=True
    ).order_by('id')

    if compteur <= 3:
        return list(operateurs[:1])

    elif compteur <= 6:
        return list(operateurs[1:2])

    else:
        return list(operateurs)


# ==========================================
# 4. ENVOYER UN EMAIL
# ==========================================

def envoyer_email(operateur, incident, alerte, delivery):

    sujet = f"Alerte laboratoire - Incident #{incident.id}"

    lien = creer_lien_reponse(delivery)

    message = f"""
Bonjour {operateur.name},

Une température anormale a été détectée dans le laboratoire.

Incident : #{incident.id}
Température : {alerte.temperature} °C
Numéro de l'alerte : {alerte.counter}
Date : {timezone.localtime(alerte.sent_at).strftime('%d/%m/%Y %H:%M:%S')}

Merci de vérifier la situation.

Pour confirmer la réception de cette alerte et envoyer un message,
cliquez sur le lien suivant :

{lien}

Système de surveillance du laboratoire.
"""

    html_message = f"""
    <html>
    <body>
        <h2>🚨 ALERTE LABORATOIRE 🚨</h2>

        <p>Bonjour {operateur.name},</p>

        <p>Une température anormale a été détectée dans le laboratoire.</p>

        <ul>
            <li><strong>Incident :</strong> #{incident.id}</li>
            <li><strong>Température :</strong> {alerte.temperature} °C</li>
            <li><strong>Numéro de l'alerte :</strong> {alerte.counter}</li>
            <li><strong>Date :</strong> {timezone.localtime(alerte.sent_at).strftime('%d/%m/%Y %H:%M:%S')}</li>
        </ul>

        <p>Merci de vérifier la situation.</p>

        <p>
            <a href="{lien}"
               style="background-color:#198754;
                      color:white;
                      padding:12px 20px;
                      text-decoration:none;
                      border-radius:5px;
                      display:inline-block;">
                J'ai bien reçu l'alerte
            </a>
        </p>

        <p>Vous pourrez également envoyer un message après avoir cliqué.</p>

        <p>Système de surveillance du laboratoire.</p>
    </body>
    </html>
    """

    send_mail(
        subject=sujet,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[operateur.email],
        html_message=html_message,
        fail_silently=False
    )


# ==========================================
# 5. ENVOYER UN MESSAGE TELEGRAM
# ==========================================

def envoyer_telegram(operateur, incident, alerte, delivery):

    token = settings.TELEGRAM_BOT_TOKEN
    chat_id = operateur.telegram_chat_id

    if not chat_id:
        raise ValueError(
            f"Aucun Chat ID Telegram pour {operateur.name}"
        )

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    lien = creer_lien_reponse(delivery)

    message = (
        f"🚨 ALERTE LABORATOIRE 🚨\n\n"
        f"Incident : #{incident.id}\n"
        f"Température : {alerte.temperature} °C\n"
        f"Alerte numéro : {alerte.counter}\n"
        f"Opérateur : {operateur.name}\n"
        f"Date : {timezone.localtime(alerte.sent_at).strftime('%d/%m/%Y %H:%M:%S')}\n\n"
        f"Merci de vérifier la situation."
    )

    response = requests.post(
        url,
        json={
            "chat_id": chat_id,
            "text": message,
            "reply_markup": {
                "inline_keyboard": [
                    [
                        {
                            "text": "J'ai bien reçu l'alerte",
                            "url": lien
                        }
                    ]
                ]
            }
        },
        timeout=10
    )

    response.raise_for_status()

    result = response.json()

    if not result.get("ok"):
        raise ValueError(
            result.get("description", "Erreur Telegram")
        )


# ==========================================
# 6. ENVOYER LES DEUX NOTIFICATIONS
# ==========================================

def notifier_operateur(operateur, incident, alerte):

    delivery = AlertDelivery.objects.create(
        alert=alerte,
        operator=operateur
    )

    erreurs = []

    # Email
    try:
        envoyer_email(
            operateur,
            incident,
            alerte,
            delivery
        )

        delivery.email_sent = True

    except Exception as e:
        erreurs.append(f"Email : {str(e)}")
        logger.exception("Erreur envoi email")

    # Telegram
    try:
        envoyer_telegram(
            operateur,
            incident,
            alerte,
            delivery
        )

        delivery.telegram_sent = True

    except Exception as e:
        erreurs.append(f"Telegram : {str(e)}")
        logger.exception("Erreur envoi Telegram")

    delivery.error_message = "\n".join(erreurs)
    delivery.save()


# ==========================================
# 7. TRAITER UNE NOUVELLE ALERTE
# ==========================================

def traiter_alerte(incident, temperature):

    if incident.status != 'ACTIVE':
        return None

    maintenant = timezone.now()

    incident.alert_count += 1
    compteur = incident.alert_count

    alerte = IncidentAlert.objects.create(
        incident=incident,
        counter=compteur,
        temperature=temperature
    )

    destinataires = obtenir_destinataires(compteur)

    for operateur in destinataires:
        notifier_operateur(
            operateur,
            incident,
            alerte
        )

    incident.next_alert_at = (
        maintenant + timedelta(minutes=INTERVALLE_ALERTE)
    )

    incident.save(
        update_fields=[
            'alert_count',
            'next_alert_at'
        ]
    )

    logger.info(
        f"Alerte #{compteur} pour incident #{incident.id}"
    )

    return alerte


# ==========================================
# 8. VERIFIER LES INCIDENTS A RAPPELER
# ==========================================

def verifier_alertes():

    maintenant = timezone.now()

    incidents = Incident.objects.filter(
        status='ACTIVE',
        next_alert_at__lte=maintenant
    )

    for incident in incidents:

        derniere_mesure = Dht11.objects.order_by('-dt').first()

        if derniere_mesure:
            temperature = derniere_mesure.temp
        else:
            temperature = incident.max_temperature

        if temperature is None:
            logger.warning(
                f"Température indisponible pour incident #{incident.id}"
            )
            continue

        traiter_alerte(incident, temperature)
