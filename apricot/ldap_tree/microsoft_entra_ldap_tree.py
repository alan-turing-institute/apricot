from apricot.oauth_clients import MicrosoftEntraClient
from apricot.proxied_ldap_entry import (
    LDAPEntryList,
    ProxiedLDAPEntry,
)

from .oauth_ldap_tree import OAuthLDAPTree


class MicrosoftEntraLDAPTree(OAuthLDAPTree):
    def __init__(self, client_id: str, client_secret: str, tenant_id: str):
        self.oauth_client = MicrosoftEntraClient(
            client_id=client_id,
            client_secret=client_secret,
            tenant_id=tenant_id,
        )
        super().__init__()

    def build_root(self, dn: str, attributes: LDAPEntryList) -> ProxiedLDAPEntry:
        return ProxiedLDAPEntry(
            dn=dn, attributes=attributes, oauth_client=self.oauth_client
        )
