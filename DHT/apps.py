
import os
import sys
import threading

from django.apps import AppConfig


class DhtConfig(AppConfig):

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'DHT'

    def ready(self):

        # Démarrer uniquement avec runserver
        if 'runserver' not in sys.argv:
            return

        # Éviter un double démarrage avec le rechargement Django
        if os.environ.get('RUN_MAIN') != 'true' and '--noreload' not in sys.argv:
            return

        from DHT.scheduler import demarrer_scheduler

        thread = threading.Thread(
            target=demarrer_scheduler,
            daemon=True
        )

        thread.start()
