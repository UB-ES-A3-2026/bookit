from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import RegexValidator
from django.db import transaction
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from usuaris.models import PerfilRepartidor, Usuari
from usuaris.validacions import (
    normalitza,
    valida_dni_nie,
    valida_matricula,
    valida_num_seguretat_social,
    valida_telefon,
)

CAMP_OBLIGATORI = "Aquest camp és obligatori."
DNI_CORREU_REGISTRAT = "DNI/correu ja registrat"
ERRORS_OBLIGATORI = {
    "blank": CAMP_OBLIGATORI,
    "required": CAMP_OBLIGATORI,
    "null": CAMP_OBLIGATORI,
}


def missatges_contrasenya(error):
    """Missatges d'una contrasenya rebutjada, tots en català.

    Django 5.2 no té la traducció catalana del missatge de contrasenya massa
    curta, així que aquest es reescriu; la resta ja arriben en català.
    """
    missatges = []
    for detall in error.error_list:
        if detall.code == "password_too_short":
            minim = detall.params["min_length"]
            missatges.append(
                "Aquesta contrasenya és massa curta. "
                f"Ha de tenir com a mínim {minim} caràcters."
            )
        else:
            missatges.extend(detall.messages)
    return missatges


class UsuariRegistreSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    rol = serializers.ChoiceField(
        source="role",
        choices=Usuari.Role.choices,
        read_only=True,
    )
    nom = serializers.CharField(
        source="name",
        max_length=150,
        error_messages={
            "blank": "Aquest camp és obligatori.",
            "required": "Aquest camp és obligatori.",
        },
    )
    correu = serializers.EmailField(
        source="email",
        validators=[
            # "iexact": ANNA@example.com i anna@example.com són el mateix correu.
            UniqueValidator(
                queryset=Usuari.objects.all(),
                message="Aquest correu electrònic ja està registrat",
                lookup="iexact",
            )
        ],
        error_messages={
            "invalid": "Introduïu una adreça de correu electrònic vàlida.",
            "required": "Aquest camp és obligatori.",
            "blank": "Aquest camp és obligatori.",
        },
    )
    adreca = serializers.CharField(
        source="address",
        error_messages={
            "blank": "Aquest camp és obligatori.",
            "required": "Aquest camp és obligatori.",
        },
    )
    num_carnet = serializers.CharField(
        source="library_card_number",
        trim_whitespace=False,
        validators=[
            RegexValidator(
                regex=r"\A[0-9]{10}\Z",
                message="El format d'aquest carnet no és vàlid",
            ),
            UniqueValidator(
                queryset=Usuari.objects.all(),
                message="Aquest usuari ja està registrat",
            ),
        ],
        error_messages={
            "blank": "Aquest camp és obligatori.",
            "required": "Aquest camp és obligatori.",
        },
    )
    contrasenya = serializers.CharField(
        source="password",
        write_only=True,
        trim_whitespace=False,
        error_messages={
            "blank": "Aquest camp és obligatori.",
            "required": "Aquest camp és obligatori.",
        },
    )

    class Meta:
        model = Usuari
        fields = (
            "id",
            "nom",
            "correu",
            "adreca",
            "num_carnet",
            "rol",
            "contrasenya",
        )

    def validate_correu(self, value):
        """Desa el correu en minúscules perquè no hi hagi duplicats per majúscules."""
        return value.lower()

    def validate(self, attrs):
        """Valida la contrasenya amb les dades de l'usuari que es vol crear.

        Es fa aquí i no al camp perquè el validador de semblança necessita el
        correu i el nom (p. ex. rebutja una contrasenya igual al correu).
        """
        dades_usuari = {
            camp: valor for camp, valor in attrs.items() if camp != "password"
        }
        try:
            validate_password(attrs["password"], user=Usuari(**dades_usuari))
        except DjangoValidationError as error:
            raise serializers.ValidationError(
                {"contrasenya": missatges_contrasenya(error)}
            ) from error
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        return Usuari.objects.create_user(password=password, **validated_data)


class RepartidorRegistreSerializer(serializers.ModelSerializer):
    """Registre d'un repartidor. Contracte a `docs/api-registre-repartidor.md`.

    Treballa sobre `Usuari`: els camps del perfil van per `perfil_repartidor`,
    així que a `validated_data` arriben agrupats sota aquesta clau.
    """

    rol = serializers.ChoiceField(
        source="role",
        choices=Usuari.Role.choices,
        read_only=True,
    )
    estat = serializers.CharField(source="perfil_repartidor.estat", read_only=True)
    nom = serializers.CharField(
        source="name",
        max_length=150,
        error_messages=ERRORS_OBLIGATORI,
    )
    cognoms = serializers.CharField(
        source="perfil_repartidor.cognoms",
        max_length=150,
        error_messages=ERRORS_OBLIGATORI,
    )
    correu = serializers.EmailField(
        source="email",
        validators=[
            UniqueValidator(
                queryset=Usuari.objects.all(),
                message=DNI_CORREU_REGISTRAT,
                lookup="iexact",
            )
        ],
        error_messages={
            **ERRORS_OBLIGATORI,
            "invalid": "Introduïu una adreça de correu electrònic vàlida.",
        },
    )
    dni = serializers.CharField(
        source="perfil_repartidor.dni",
        validators=[valida_dni_nie],
        error_messages=ERRORS_OBLIGATORI,
    )
    telefon = serializers.CharField(
        source="perfil_repartidor.telefon",
        validators=[valida_telefon],
        error_messages=ERRORS_OBLIGATORI,
    )
    # allow_blank: així un vehicle buit dona "obligatori" (validate_vehicle) i no
    # l'error d'opció no vàlida, que és el que retorna ChoiceField per defecte.
    vehicle = serializers.ChoiceField(
        source="perfil_repartidor.vehicle",
        choices=PerfilRepartidor.Vehicle.choices,
        allow_blank=True,
        error_messages={
            **ERRORS_OBLIGATORI,
            "invalid_choice": '"bici", "moto" o "cotxe" no és una opció vàlida.',
        },
    )
    matricula = serializers.CharField(
        source="perfil_repartidor.matricula",
        required=False,
        allow_blank=True,
        allow_null=True,
        validators=[valida_matricula],
    )
    num_seguretat_social = serializers.CharField(
        source="perfil_repartidor.num_seguretat_social",
        validators=[valida_num_seguretat_social],
        error_messages=ERRORS_OBLIGATORI,
    )
    contrasenya = serializers.CharField(
        source="password",
        write_only=True,
        trim_whitespace=False,
        error_messages=ERRORS_OBLIGATORI,
    )

    class Meta:
        model = Usuari
        fields = (
            "id",
            "nom",
            "cognoms",
            "correu",
            "dni",
            "telefon",
            "vehicle",
            "matricula",
            "num_seguretat_social",
            "rol",
            "estat",
            "contrasenya",
        )

    def validate_correu(self, value):
        """Desa el correu en minúscules perquè no hi hagi duplicats per majúscules."""
        return value.lower()

    def validate_dni(self, value):
        """Normalitza el DNI/NIE abans de comprovar que no estigui registrat."""
        dni = normalitza(value)
        if PerfilRepartidor.objects.filter(dni=dni).exists():
            raise serializers.ValidationError(DNI_CORREU_REGISTRAT)
        return dni

    def validate_telefon(self, value):
        return normalitza(value)

    def validate_vehicle(self, value):
        if not value:
            raise serializers.ValidationError(CAMP_OBLIGATORI)
        return value

    def validate_matricula(self, value):
        return normalitza(value)

    def validate_num_seguretat_social(self, value):
        return normalitza(value)

    def validate(self, attrs):
        """Comprova la matrícula segons el vehicle i la contrasenya."""
        perfil = attrs["perfil_repartidor"]
        errors = {}

        if perfil["vehicle"] == PerfilRepartidor.Vehicle.BICI:
            perfil["matricula"] = ""
        elif not perfil.get("matricula"):
            errors["matricula"] = [CAMP_OBLIGATORI]

        try:
            validate_password(
                attrs["password"],
                user=Usuari(email=attrs["email"], name=attrs["name"]),
            )
        except DjangoValidationError as error:
            errors["contrasenya"] = missatges_contrasenya(error)

        if errors:
            raise serializers.ValidationError(errors)
        return attrs

    def create(self, validated_data):
        """Crea l'usuari i el seu perfil; si un dels dos falla, no es desa res."""
        perfil = validated_data.pop("perfil_repartidor")
        password = validated_data.pop("password")
        with transaction.atomic():
            usuari = Usuari.objects.create_user(
                password=password,
                role=Usuari.Role.REPARTIDOR,
                # Un repartidor no té carnet, però el camp és únic i no admet
                # nuls. El DNI fa el valor únic i mai coincideix amb un carnet
                # real, que són 10 xifres.
                library_card_number=f"repartidor-{perfil['dni']}",
                **validated_data,
            )
            PerfilRepartidor.objects.create(usuari=usuari, **perfil)
        return usuari
