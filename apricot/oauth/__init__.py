from apricot.types import LDAPAttributeDict, LDAPControlTuple

from .enums import OAuthBackend
from .keycloak_client import KeycloakClient
from .microsoft_entra_client import MicrosoftEntraClient
from .oauth_client import OAuthClient
from .oauth_data_adaptor import OAuthDataAdaptor

OAuthClientMap = {
    OAuthBackend.MICROSOFT_ENTRA: MicrosoftEntraClient,
    OAuthBackend.KEYCLOAK: KeycloakClient,
}

__all__ = [
    "LDAPAttributeDict",
    "LDAPControlTuple",
    "OAuthBackend",
    "OAuthClient",
    "OAuthClientMap",
    "OAuthDataAdaptor",
]
