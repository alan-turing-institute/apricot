from apricot.typedefs import LDAPAttributeDict, LDAPControlTuple

from .enums import OAuthBackend
from .keycloak_client import KeycloakClient
from .microsoft_entra_client import MicrosoftEntraClient
from .oauth_client import OAuthClient
from .oauth_data_adaptor import OAuthDataAdaptor
from .zitadel_client import ZitadelClient

OAuthClientMap = {
    OAuthBackend.MICROSOFT_ENTRA: MicrosoftEntraClient,
    OAuthBackend.KEYCLOAK: KeycloakClient,
    OAuthBackend.ZITADEL: ZitadelClient,
}

__all__ = [
    "LDAPAttributeDict",
    "LDAPControlTuple",
    "OAuthBackend",
    "OAuthClient",
    "OAuthClientMap",
    "OAuthDataAdaptor",
]
