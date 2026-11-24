from django.conf import settings
from rest_framework import serializers

from cataleg.models import Llibre
from prestecs.models import Comanda, Notificacio, Prestec
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
TIPUS_LLIURAMENT_INVALID = "Tria lliurament a domicili o recollida a la biblioteca."
ADRECA_OBLIGATORIA = "Indica l'adreça de lliurament."

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
        fields = (
            "id",
            "estat",
            "biblioteca",
            "llibres",
            "tipus_lliurament",
            "adreca_lliurament",
            "cost_enviament",
            "data_lliurament",
            "creada",
        )

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


class PrestecSerializer(serializers.ModelSerializer):
    """Un llibre que l'usuari té en préstec (US19-T2)."""

    llibre = LlibreComandaSerializer()
    biblioteca = serializers.SerializerMethodField()
    termini_superat = serializers.SerializerMethodField()

    class Meta:
        model = Prestec
        fields = ("id", "llibre", "biblioteca", "data_inici", "data_limit", "termini_superat")

    def get_biblioteca(self, prestec):
        return {"id": prestec.biblioteca_id, "nom": prestec.biblioteca.biblioteca.nom}

    def get_termini_superat(self, prestec):
        return prestec.termini_superat()


class ConfirmacioComandaSerializer(serializers.Serializer):
    """Dades per confirmar una comanda: la biblioteca, els llibres i com es lliura.

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
    tipus_lliurament = serializers.ChoiceField(
        choices=Comanda.TipusLliurament.choices,
        default=Comanda.TipusLliurament.DOMICILI,
        error_messages={"invalid_choice": TIPUS_LLIURAMENT_INVALID, "null": TIPUS_LLIURAMENT_INVALID},
    )
    # Si no s'envia, és null o és buida, es porta a l'adreça del perfil de l'usuari.
    adreca_lliurament = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=""
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

    def validate(self, dades):
        if dades["tipus_lliurament"] == Comanda.TipusLliurament.RECOLLIDA:
            dades["adreca_lliurament"] = ""
            return dades

        adreca = dades["adreca_lliurament"] or self.context["request"].user.address
        if not adreca.strip():
            raise serializers.ValidationError({"adreca_lliurament": [ADRECA_OBLIGATORIA]})
        dades["adreca_lliurament"] = adreca.strip()
        return dades


class NotificacioSerializer(serializers.ModelSerializer):
    """Una notificació de l'usuari (US8-T3)."""

    class Meta:
        model = Notificacio
        fields = ("id", "comanda", "text", "llegida", "creada")


def coordenada(valor):
    """Coordenada com a número JSON (no com a text, com faria `DecimalField`)."""
    return float(valor) if valor is not None else None


class LlibreParadaSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    titol = serializers.CharField(read_only=True)
    autor = serializers.CharField(read_only=True)
    portada = serializers.CharField(read_only=True)


class ParadaRutaSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    ordre = serializers.IntegerField(read_only=True)
    tipus = serializers.CharField(read_only=True)
    comanda = serializers.IntegerField(source="comanda_id", read_only=True)
    estat = serializers.CharField(source="comanda.estat", read_only=True)
    llibres = serializers.SerializerMethodField()
    adreca = serializers.SerializerMethodField()

    def get_llibres(self, parada):
        linies = parada.comanda.linies.all()
        llibres = [linia.llibre for linia in linies]
        return LlibreParadaSerializer(llibres, many=True).data

    def get_adreca(self, parada):
        comanda = parada.comanda

        # Les coordenades són per al mapa de la ruta (US12-T13); valen `null` si no
        # se saben, i llavors la parada només surt a la llista.
        if parada.tipus == "recollida":
            biblioteca = comanda.biblioteca.biblioteca
            return {
                "biblioteca": {
                    "id": comanda.biblioteca_id,
                    "nom": biblioteca.nom,
                },
                "text": None,
                "latitud": coordenada(biblioteca.latitud),
                "longitud": coordenada(biblioteca.longitud),
            }

        return {
            "biblioteca": None,
            # Les comandes anteriors a `adreca_lliurament` no la tenen desada.
            "text": comanda.adreca_lliurament or comanda.usuari.address,
            "latitud": coordenada(comanda.latitud_lliurament),
            "longitud": coordenada(comanda.longitud_lliurament),
        }
