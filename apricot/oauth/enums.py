from enum import Enum


class OAuthBackend(str, Enum):
    """Available OAuth backends."""

    MICROSOFT_ENTRA = "MicrosoftEntra"
    KEYCLOAK = "Keycloak"
