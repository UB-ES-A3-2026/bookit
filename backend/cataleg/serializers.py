from rest_framework import serializers

from cataleg.models import Llibre


class LlibreCercaSerializer(serializers.ModelSerializer):
    disponible = serializers.BooleanField(read_only=True)
    mitjana_valoracions = serializers.FloatField(read_only=True, allow_null=True)
    nombre_valoracions = serializers.IntegerField(read_only=True)

    class Meta:
        model = Llibre
        fields = [
            "id",
            "titol",
            "autor",
            "isbn",
            "portada",
            "disponible",
            "mitjana_valoracions",
            "nombre_valoracions",
        ]
