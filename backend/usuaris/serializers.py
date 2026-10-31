from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import RegexValidator
from django.db import IntegrityError
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from usuaris.models import Usuari

PASSWORD_FIELD = "password"
REQUIRED = "Aquest camp " + chr(233) + "s obligatori."
EMAIL_DUPLICATE = "Aquest correu electr" + chr(242) + "nic ja est" + chr(224) + " registrat"
EMAIL_INVALID = "Introdu" + chr(239) + "u una adre" + chr(231) + "a de correu electr" + chr(242) + "nic v" + chr(224) + "lida."
CARD_INVALID = "El format d" + chr(8217) + "aquest carnet no " + chr(233) + "s v" + chr(224) + "lid"
CARD_DUPLICATE = "Aquest usuari ja est" + chr(224) + " registrat"


class UsuariRegistreSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    rol = serializers.ChoiceField(source="role", choices=Usuari.Role.choices, read_only=True)
    nom = serializers.CharField(source="name", max_length=150, error_messages={"blank": REQUIRED, "required": REQUIRED})
    correu = serializers.EmailField(source="email", validators=[UniqueValidator(queryset=Usuari.objects.all(), message=EMAIL_DUPLICATE, lookup="iexact")], error_messages={"invalid": EMAIL_INVALID, "required": REQUIRED, "blank": REQUIRED})
    adreca = serializers.CharField(source="address", error_messages={"blank": REQUIRED, "required": REQUIRED})
    num_carnet = serializers.CharField(source="library_card_number", trim_whitespace=False, validators=[RegexValidator(regex=r"\A[0-9]{10}\Z", message=CARD_INVALID), UniqueValidator(queryset=Usuari.objects.all(), message=CARD_DUPLICATE)], error_messages={"blank": REQUIRED, "required": REQUIRED})
    contrasenya = serializers.CharField(source=PASSWORD_FIELD, write_only=True, trim_whitespace=False, error_messages={"blank": REQUIRED, "required": REQUIRED})

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
        secret = validated_data.pop(PASSWORD_FIELD)
        email = validated_data.pop("email")
        try:
            return Usuari.objects.create_user(email, secret, **validated_data)
        except IntegrityError as exc:
            if Usuari.objects.filter(email__iexact=email).exists():
                raise serializers.ValidationError({"correu": [EMAIL_DUPLICATE]}) from exc
            if Usuari.objects.filter(library_card_number=validated_data["library_card_number"]).exists():
                raise serializers.ValidationError({"num_carnet": [CARD_DUPLICATE]}) from exc
            raise
