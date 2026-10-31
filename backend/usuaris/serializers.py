from uuid import uuid4

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import RegexValidator
from django.db import transaction
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from usuaris.models import Biblioteca, Usuari


CAMPS_BIBLIOTECA_INVALIDS = (
    "Algún dels camps no és vàlid o no s'ha introduït, torna a intentar-ho"
)
CORREU_BIBLIOTECA_DUPLICAT = (
    "Aquest correu correspon a un compte existent, torna a probar amb un altre correu"
)


def missatges_contrasenya(error):
    """Missatges d'una contrasenya rebutjada, tots en català."""
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
        return value.lower()

    def validate(self, attrs):
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
        return Usuari.objects.create_user(
            password=password,
            **validated_data,
        )


class BibliotecaRegistreSerializer(serializers.Serializer):
    nom = serializers.CharField(
        max_length=150,
        error_messages={
            "blank": CAMPS_BIBLIOTECA_INVALIDS,
            "required": CAMPS_BIBLIOTECA_INVALIDS,
        },
    )
    correu = serializers.EmailField(
        error_messages={
            "blank": CAMPS_BIBLIOTECA_INVALIDS,
            "required": CAMPS_BIBLIOTECA_INVALIDS,
            "invalid": CAMPS_BIBLIOTECA_INVALIDS,
        },
    )

    def validate_correu(self, value):
        if Usuari.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(CORREU_BIBLIOTECA_DUPLICAT)
        return value.lower()

    def create(self, validated_data):
        with transaction.atomic():
            usuari = Usuari.objects.create_user(
                validated_data["correu"],
                None,
                {
                    "name": validated_data["nom"],
                    "address": "",
                    "library_card_number": f"biblioteca-{uuid4().hex}",
                    "role": Usuari.Role.BIBLIOTECA,
                    "is_active": False,
                },
            )
            return Biblioteca.objects.create(
                usuari=usuari,
                nom=validated_data["nom"],
            )

    def to_representation(self, instance):
        return {
            "nom": instance.nom,
            "correu": instance.usuari.email,
        }
