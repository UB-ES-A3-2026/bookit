from django.db import IntegrityError, transaction
from rest_framework import serializers

from cataleg.models import ExemplarBiblioteca, Llibre
from cataleg.validacions import ISBN_INVALID, es_isbn_valid, normalitza_isbn


class LlibreCercaSerializer(serializers.ModelSerializer):
    disponible = serializers.BooleanField(read_only=True)
    mitjana_valoracions = serializers.FloatField(
        source="mitjana_valoracions_cerca",
        read_only=True,
        allow_null=True,
    )
    nombre_valoracions = serializers.IntegerField(
        source="nombre_valoracions_cerca",
        read_only=True,
    )

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


CAMPS_OBLIGATORIS = "Omple tots els camps obligatoris per continuar"
LLIBRE_JA_AL_CATALEG = "Aquest llibre ja és al teu catàleg, actualitza'n els exemplars"
ERRORS_OBLIGATORI = {
    "required": CAMPS_OBLIGATORIS,
    "blank": CAMPS_OBLIGATORIS,
    "null": CAMPS_OBLIGATORIS,
}


class EnterObligatori(serializers.IntegerField):
    """Enter obligatori que, com els camps de text, tracta `""` i els espais com un camp buit."""

    def to_internal_value(self, data):
        if isinstance(data, str) and not data.strip():
            self.fail("blank")
        return super().to_internal_value(data)


class LlibreCatalegSerializer(serializers.Serializer):
    """Llibre del catàleg d'una biblioteca (US17-T3). Contracte a `docs/api-cataleg.md`.

    Treballa amb la fila `ExemplarBiblioteca` de la biblioteca autenticada, que es
    rep a `context["request"].user`, i la mostra amb les dades del llibre.
    """

    id = serializers.IntegerField(read_only=True)
    titol = serializers.CharField(max_length=255, error_messages=ERRORS_OBLIGATORI)
    autor = serializers.CharField(max_length=255, error_messages=ERRORS_OBLIGATORI)
    isbn = serializers.CharField(error_messages=ERRORS_OBLIGATORI)
    portada = serializers.URLField(
        max_length=200, required=False, allow_blank=True, default=""
    )
    exemplars = EnterObligatori(min_value=1, error_messages=ERRORS_OBLIGATORI)

    def to_representation(self, exemplar):
        llibre = exemplar.llibre
        return {
            "id": llibre.id,
            "titol": llibre.titol,
            "autor": llibre.autor,
            "isbn": llibre.isbn,
            "portada": llibre.portada,
            "exemplars": exemplar.quantitat,
        }

    def validate_isbn(self, valor):
        if not es_isbn_valid(valor):
            raise serializers.ValidationError(ISBN_INVALID)
        isbn = normalitza_isbn(valor)
        biblioteca = self.context["request"].user
        if ExemplarBiblioteca.objects.filter(
            biblioteca=biblioteca, llibre__isbn=isbn
        ).exists():
            raise serializers.ValidationError(LLIBRE_JA_AL_CATALEG)
        return isbn

    def create(self, validated_data):
        """Afegeix el llibre al catàleg i reaprofita el `Llibre` si ja existeix per l'ISBN.

        Si el llibre ja existeix, se'n mantenen les dades desades (P2 del contracte).
        """
        biblioteca = self.context["request"].user
        llibre, _ = Llibre.objects.get_or_create(
            isbn=validated_data["isbn"],
            defaults={
                "titol": validated_data["titol"],
                "autor": validated_data["autor"],
                "portada": validated_data["portada"],
            },
        )
        try:
            with transaction.atomic():
                return ExemplarBiblioteca.objects.create(
                    llibre=llibre,
                    biblioteca=biblioteca,
                    quantitat=validated_data["exemplars"],
                )
        except IntegrityError:
            # Dues peticions iguals alhora: la segona topa amb la restricció única.
            raise serializers.ValidationError({"isbn": [LLIBRE_JA_AL_CATALEG]})
