
import logging

from rest_framework.decorators import api_view
from rest_framework import generics
from rest_framework.response import Response

from .models import Dht11
from .serializers import DHT11serialize
from .incident_service import traiter_mesure


logger = logging.getLogger(__name__)


@api_view(['GET'])
def Dlist(request):
    all_data = Dht11.objects.all()
    data = DHT11serialize(all_data, many=True).data

    return Response({'data': data})


class Dhtviews(generics.CreateAPIView):
    queryset = Dht11.objects.all()
    serializer_class = DHT11serialize

    def perform_create(self, serializer):

        # 1. Enregistrer la mesure du capteur
        mesure = serializer.save()

        # 2. Traiter l'incident selon la température
        incident = traiter_mesure(mesure)

        # 3. Journaliser le résultat
        if incident:
            logger.info(
                f"Incident actif #{incident.id} "
                f"| Température : {mesure.temp} °C"
            )
        else:
            logger.info(
                f"Température normale : {mesure.temp} °C"
            )
