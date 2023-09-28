from .enums import OAuthBackend
from .microsoft_entra_client import MicrosoftEntraClient
from .oauth_client import OAuthClient
from .types import LDAPAttributeDict

OAuthClientMap = {OAuthBackend.MICROSOFT_ENTRA: MicrosoftEntraClient}

__all__ = [
    "LDAPAttributeDict",
    "OAuthBackend",
    "OAuthClient",
    "OAuthClientMap",
]
