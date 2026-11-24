
from rest_framework import serializers
from .models import Dht11

class DHT11serialize(serializers.ModelSerializer):

    temperature = serializers.FloatField(
        source='temp',
        write_only=True
    )

    humidity = serializers.FloatField(
        source='hum',
        write_only=True
    )

    class Meta:
        model = Dht11
        fields = ['id', 'temperature', 'humidity', 'temp', 'hum', 'dt']
        read_only_fields = ['id', 'temp', 'hum', 'dt']
