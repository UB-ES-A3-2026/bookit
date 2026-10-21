from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import RegexValidator
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from usuaris.models import Usuari


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
