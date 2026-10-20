from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import RegexValidator
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from usuaris.models import Usuari


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

    def validate_contrasenya(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as error:
            raise serializers.ValidationError(error.messages) from error
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        return Usuari.objects.create_user(password=password, **validated_data)
