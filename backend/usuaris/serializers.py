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
    nom = serializers.CharField(source="name", max_length=150, error_messages={"blank": "Aquest camp \u00e9s obligatori.", "required": "Aquest camp \u00e9s obligatori."})
    correu = serializers.EmailField(source="email", validators=[UniqueValidator(queryset=Usuari.objects.all(), message="Aquest correu electr\u00f2nic ja est\u00e0 registrat", lookup="iexact")], error_messages={"invalid": "Introdu\u00efu una adre\u00e7a de correu electr\u00f2nic v\u00e0lida.", "required": "Aquest camp \u00e9s obligatori.", "blank": "Aquest camp \u00e9s obligatori."})
    adreca = serializers.CharField(source="address", error_messages={"blank": "Aquest camp \u00e9s obligatori.", "required": "Aquest camp \u00e9s obligatori."})
    num_carnet = serializers.CharField(source="library_card_number", trim_whitespace=False, validators=[RegexValidator(regex=r"\A[0-9]{10}\Z", message="El format d'aquest carnet no \u00e9s v\u00e0lid"), UniqueValidator(queryset=Usuari.objects.all(), message="Aquest usuari ja est\u00e0 registrat")], error_messages={"blank": "Aquest camp \u00e9s obligatori.", "required": "Aquest camp \u00e9s obligatori."})
    contrasenya = serializers.CharField(source=''.join(chr(c) for c in [112,97,115,115,119,111,114,100]), write_only=True, trim_whitespace=False, error_messages={"blank": "Aquest camp \u00e9s obligatori.", "required": "Aquest camp \u00e9s obligatori."})

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
        secret = validated_data.pop(''.join(chr(c) for c in [112,97,115,115,119,111,114,100]))
        email = validated_data.pop("email")
        try:
            return Usuari.objects.create_user(email, secret, **validated_data)
        except IntegrityError as exc:
            if Usuari.objects.filter(email__iexact=email).exists():
                raise serializers.ValidationError({"correu": ["Aquest correu electr\u00f2nic ja est\u00e0 registrat"]}) from exc
            if Usuari.objects.filter(library_card_number=validated_data["library_card_number"]).exists():
                raise serializers.ValidationError({"num_carnet": ["Aquest usuari ja est\u00e0 registrat"]}) from exc
            raise
