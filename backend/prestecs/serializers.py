from django.conf import settings
from rest_framework import serializers

from cataleg.models import Llibre
from prestecs.models import Comanda
from usuaris.models import Usuari

# Missatges del contracte (docs/api-comandes.md). Els del límit i l'estoc són
# literals dels criteris d'acceptació de la US6.
CAMP_OBLIGATORI = "Aquest camp és obligatori."
LLISTA_BUIDA = "Afegeix almenys un llibre a la comanda."
LLIBRE_REPETIT = "Un llibre no pot sortir dues vegades a la mateixa comanda."
BIBLIOTECA_INEXISTENT = "La biblioteca no existeix."
LLIBRE_INEXISTENT = "Algun dels llibres no existeix."
LIMIT_SUPERAT = "Has superat el límit de llibres per aquesta comanda, elimina un per continuar"
SENSE_ESTOC = "Aquest llibre no te estoc en aquest moment. Pots apuntar-te a la llista d'espera"

ERRORS_OBLIGATORI = {"required": CAMP_OBLIGATORI, "null": CAMP_OBLIGATORI}


class LlibreComandaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Llibre
        fields = ("id", "titol", "autor", "portada")


class ComandaSerializer(serializers.ModelSerializer):
    """Format d'una comanda a les respostes de l'API."""

    biblioteca = serializers.SerializerMethodField()
    llibres = serializers.SerializerMethodField()

    class Meta:
        model = Comanda
        fields = ("id", "estat", "biblioteca", "llibres", "data_lliurament", "creada")

    def get_biblioteca(self, comanda):
        return {"id": comanda.biblioteca_id, "nom": comanda.biblioteca.biblioteca.nom}

    def get_llibres(self, comanda):
        # `all()` aprofita les línies ja carregades amb `prefetch_related` a les llistes.
        linies = sorted(comanda.linies.all(), key=lambda linia: linia.pk)
        return LlibreComandaSerializer([linia.llibre for linia in linies], many=True).data


class ComandaBibliotecaSerializer(ComandaSerializer):
    """Comanda tal com la veu la biblioteca: també diu de quin usuari és (US10)."""

    usuari = serializers.SerializerMethodField()

    class Meta(ComandaSerializer.Meta):
        fields = ("id", "estat", "usuari", "biblioteca", "llibres", "data_lliurament", "creada")

    def get_usuari(self, comanda):
        return {"id": comanda.usuari_id, "nom": comanda.usuari.name}


class ConfirmacioComandaSerializer(serializers.Serializer):
    """Dades per confirmar una comanda: la biblioteca i els llibres.

    Aquí es comprova el format de la petició. L'estoc es comprova en crear la
    comanda (`prestecs.serveis.confirma_comanda`), dins de la mateixa transacció.
    """

    biblioteca = serializers.IntegerField(
        error_messages={**ERRORS_OBLIGATORI, "invalid": BIBLIOTECA_INEXISTENT}
    )
    # Sense `child`: si un element no és un número, l'error ha de ser el mateix
    # missatge en una llista, no un error per posició (vegeu `validate_llibres`).
    llibres = serializers.ListField(
        error_messages={**ERRORS_OBLIGATORI, "not_a_list": LLIBRE_INEXISTENT},
    )

    def validate_biblioteca(self, id_biblioteca):
        biblioteca = Usuari.objects.filter(
            pk=id_biblioteca,
            role=Usuari.Role.BIBLIOTECA,
            is_active=True,
            biblioteca__isnull=False,
        ).first()
        if biblioteca is None:
            raise serializers.ValidationError(BIBLIOTECA_INEXISTENT)
        return biblioteca

    def validate_llibres(self, ids):
        """Retorna els llibres en el mateix ordre en què s'han enviat."""
        if not ids:
            raise serializers.ValidationError(LLISTA_BUIDA)
        # `bool` és un `int` a Python, però `true` no és l'id de cap llibre.
        if any(isinstance(id_llibre, bool) or not isinstance(id_llibre, int) for id_llibre in ids):
            raise serializers.ValidationError(LLIBRE_INEXISTENT)
        if len(set(ids)) != len(ids):
            raise serializers.ValidationError(LLIBRE_REPETIT)

        llibres = Llibre.objects.in_bulk(ids)
        if len(llibres) != len(ids):
            raise serializers.ValidationError(LLIBRE_INEXISTENT)
        if len(ids) > settings.LIMIT_LLIBRES_COMANDA:
            raise serializers.ValidationError(LIMIT_SUPERAT)
        return [llibres[id_llibre] for id_llibre in ids]
