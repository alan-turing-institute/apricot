from apricot.oauth_clients import MicrosoftEntraClient

from .oauth_ldap_tree import OAuthLDAPTree


class MicrosoftEntraLDAPTree(OAuthLDAPTree):
    def __init__(self, client_id: str, client_secret: str, tenant_id: str):
        self.oauth_client = MicrosoftEntraClient(
            client_id=client_id,
            client_secret=client_secret,
            tenant_id=tenant_id,
        )
        super().__init__()
