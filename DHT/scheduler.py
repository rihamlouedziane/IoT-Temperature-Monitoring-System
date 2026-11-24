
import time
import logging

from DHT.alert_service import verifier_alertes

logger = logging.getLogger(__name__)


def demarrer_scheduler():

    logger.info("Scheduler des alertes démarré.")

    while True:
        try:
            verifier_alertes()

        except Exception:
            logger.exception(
                "Erreur pendant la vérification des alertes."
            )

        time.sleep(60)
