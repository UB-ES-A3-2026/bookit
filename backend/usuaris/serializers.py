from uuid import uuid4

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import RegexValidator
from django.core.mail import send_mail
from django.db import transaction
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.serializers import (
    PasswordField,
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)

from usuaris.models import Biblioteca, PerfilRepartidor, Usuari
from usuaris.validacions import (
    normalitza,
    valida_dni_nie,
    valida_matricula,
    valida_num_seguretat_social,
    valida_telefon,
)

CAMP_OBLIGATORI = "Aquest camp és obligatori."
VERIFICA_CORREU = "Verifica el teu correu"
# Missatges de l'inici de sessió d'un repartidor que encara no pot entrar.
MISSATGES_ESTAT_REPARTIDOR = {
    PerfilRepartidor.Estat.PENDENT: "Pendent de validació",
    PerfilRepartidor.Estat.REBUTJAT: "Validació incompleta",
}
CORREU_INVALID = "Introduïu una adreça de correu electrònic vàlida."
DNI_CORREU_REGISTRAT = "DNI/correu ja registrat"
ERRORS_OBLIGATORI = {
    "blank": CAMP_OBLIGATORI,
    "required": CAMP_OBLIGATORI,
    "null": CAMP_OBLIGATORI,
}


def neteja_correu(correu):
    """Retorna el correu en minúscules, perquè no hi hagi duplicats per majúscules.

    El límit es comprova aquí i no amb `max_length` perquè, a partir de 320
    caràcters, EmailField també el rebutja i el missatge sortiria repetit.
    """
    if len(correu) > Usuari._meta.get_field("email").max_length:
        raise serializers.ValidationError(CORREU_INVALID)
    return correu.lower()


CAMPS_BIBLIOTECA_INVALIDS = (
    "Algún dels camps no és vàlid o no s'ha introduït, torna a intentar-ho"
)
CORREU_BIBLIOTECA_DUPLICAT = (
    "Aquest correu correspon a un compte existent, torna a probar amb un altre correu"
)


def enviar_correu_verificacio(usuari):
    """Envia l'enllaç per verificar el correu i triar la contrasenya del compte.

    L'enllaç porta a la pàgina de verificació del frontend, que és on la
    biblioteca tria la contrasenya i activa el compte.
    """
    uid = urlsafe_base64_encode(force_bytes(usuari.pk))
    token = default_token_generator.make_token(usuari)
    enllac = f"{settings.FRONTEND_URL}/verificacio/biblioteca/{uid}/{token}"
    send_mail(
        "Verifica el teu compte de biblioteca",
        (
            f"Hola {usuari.name},\n\n"
            "Verifica el correu i tria la contrasenya del teu compte de "
            "biblioteca amb aquest enllaç:\n"
            f"{enllac}\n\n"
            "Aquest enllaç caduca en 24 hores."
        ),
        settings.DEFAULT_FROM_EMAIL,
        [usuari.email],
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
            "invalid": CORREU_INVALID,
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
        return neteja_correu(value)

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
        return Usuari.objects.create_user(password=password, **validated_data)


class IniciSessioSerializer(TokenObtainPairSerializer):
    """Credencials d'inici de sessió: `correu` i `contrasenya`, com a la resta de l'API.

    Els camps públics es tradueixen a `email` i `password`, que són els que
    simplejwt fa servir per autenticar l'usuari.
    """

    default_error_messages = {
        "no_active_account": "El correu o la contrasenya no són correctes.",
    }

    correu = serializers.CharField(
        source="email",
        write_only=True,
        error_messages={
            "required": "Aquest camp és obligatori.",
            "blank": "Aquest camp és obligatori.",
        },
    )
    contrasenya = PasswordField(
        source="password",
        error_messages={
            "required": "Aquest camp és obligatori.",
            "blank": "Aquest camp és obligatori.",
        },
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # simplejwt els afegeix en crear el serializer; aquí els substitueixen els camps en català.
        del self.fields["email"]
        del self.fields["password"]

    def validate_correu(self, value):
        """Passa el correu a minúscules, que és com el desa el registre."""
        return value.lower()

    def validate(self, attrs):
        """Retorna els tokens només si l'estat del compte permet entrar (US2-T3).

        Amb les credencials correctes però un compte que no pot entrar, respon 403
        amb el motiu. Amb una contrasenya incorrecta sempre es respon el 401
        genèric, perquè ningú pugui esbrinar l'estat d'un compte aliè.
        """
        try:
            dades = super().validate(attrs)
        except AuthenticationFailed:
            self.comprova_biblioteca_sense_verificar(attrs["email"], attrs["password"])
            raise
        self.comprova_estat_repartidor(self.user)
        return dades

    @staticmethod
    def comprova_biblioteca_sense_verificar(correu, contrasenya):
        """Django no autentica els comptes inactius, així que la contrasenya es comprova aquí.

        Una biblioteca té el compte inactiu fins que verifica el correu.
        """
        biblioteca = Usuari.objects.filter(
            email=correu, role=Usuari.Role.BIBLIOTECA, is_active=False
        ).first()
        if biblioteca is not None and biblioteca.check_password(contrasenya):
            raise PermissionDenied(VERIFICA_CORREU)

    @staticmethod
    def comprova_estat_repartidor(usuari):
        """Rebutja els repartidors amb el perfil pendent o rebutjat."""
        try:
            estat = usuari.perfil_repartidor.estat
        except PerfilRepartidor.DoesNotExist:
            return
        if estat in MISSATGES_ESTAT_REPARTIDOR:
            raise PermissionDenied(MISSATGES_ESTAT_REPARTIDOR[estat])


class UsuariActualSerializer(serializers.ModelSerializer):
    """Dades de l'usuari autenticat: els mateixos camps per als tres rols.

    No inclou `adreca` ni `num_carnet`: només tenen sentit per al rol `usuari` i
    el carnet dels altres rols és intern (vegeu `docs/api-auth.md`).
    """

    nom = serializers.CharField(source="name", read_only=True)
    correu = serializers.EmailField(source="email", read_only=True)
    rol = serializers.CharField(source="role", read_only=True)

    class Meta:
        model = Usuari
        fields = ("id", "nom", "correu", "rol")


class RenovacioTokenSerializer(TokenRefreshSerializer):
    """Renovació del token d'accés que també rebutja els comptes esborrats.

    simplejwt busca l'usuari del token de refresc amb `get()` i, si el compte ja
    no existeix, la petició acaba en un error 500. Aquí es respon 401, com amb un
    compte desactivat.
    """

    def validate(self, attrs):
        try:
            return super().validate(attrs)
        except Usuari.DoesNotExist:
            raise AuthenticationFailed(
                self.error_messages["no_active_account"], "no_active_account"
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
            "invalid": CORREU_INVALID,
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
        return neteja_correu(value)

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
