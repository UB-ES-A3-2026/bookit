from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import RegexValidator
from django.db import IntegrityError
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from usuaris.models import Usuari


class UsuariRegistreSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    rol = serializers.ChoiceField(source="role", choices=Usuari.Role.choices, read_only=True)
    nom = serializers.CharField(
        source="name",
        max_length=150,
        error_messages={"blank": "Aquest camp ?s obligatori.", "required": "Aquest camp ?s obligatori."},
    )
    correu = serializers.EmailField(
        source="email",
        validators=[UniqueValidator(
            queryset=Usuari.objects.all(),
            message="Aquest correu electr?nic ja est? registrat",
            lookup="iexact",
        )],
        error_messages={
            "invalid": "Introdu?u una adre?a de correu electr?nic v?lida.",
            "required": "Aquest camp ?s obligatori.",
            "blank": "Aquest camp ?s obligatori.",
        },
    )
    adreca = serializers.CharField(
        source="address",
        error_messages={"blank": "Aquest camp ?s obligatori.", "required": "Aquest camp ?s obligatori."},
    )
    num_carnet = serializers.CharField(
        source="library_card_number",
        trim_whitespace=False,
        validators=[
            RegexValidator(regex=r"\A[0-9]{10}\Z", message="El format d'aquest carnet no ?s v?lid"),
            UniqueValidator(queryset=Usuari.objects.all(), message="Aquest usuari ja est? registrat"),
        ],
        error_messages={"blank": "Aquest camp ?s obligatori.", "required": "Aquest camp ?s obligatori."},
    )
    contrasenya = serializers.CharField(
        source="password",
        write_only=True,
        trim_whitespace=False,
        error_messages={"blank": "Aquest camp ?s obligatori.", "required": "Aquest camp ?s obligatori."},
    )

    class Meta:
        model = Usuari
        fields = ("id", "nom", "correu", "adreca", "num_carnet", "rol", "contrasenya")

    def validate_correu(self, value):
        return value.lower()

    def validate_contrasenya(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as error:
            raise serializers.ValidationError(error.messages) from error
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        email = validated_data.pop("email")
        try:
            return Usuari.objects.create_user(email=email, password=password, **validated_data)
        except IntegrityError as exc:
            if Usuari.objects.filter(email__iexact=email).exists():
                raise serializers.ValidationError({
                    "correu": ["Aquest correu electr?nic ja est? registrat"]
                }) from exc
            if Usuari.objects.filter(
                library_card_number=validated_data["library_card_number"]
            ).exists():
                raise serializers.ValidationError({
                    "num_carnet": ["Aquest usuari ja est? registrat"]
                }) from exc
            raise
