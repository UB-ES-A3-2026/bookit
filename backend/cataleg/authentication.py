from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken


class AutenticacioJWTOpcional(JWTAuthentication):
    """Autentica JWT vàlids i tracta els tokens absents o invàlids com a anònims."""

    def authenticate(self, request):
        try:
            return super().authenticate(request)
        except (AuthenticationFailed, InvalidToken):
            return None
