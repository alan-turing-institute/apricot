from ldaptor.interfaces import IConnectedLDAPEntry, ILDAPEntry
from ldaptor.protocols.ldap.distinguishedname import DistinguishedName
from twisted.internet import defer
from zope.interface import implementer

from apricot.oauth_clients import MicrosoftEntraClient, OAuthClient
from apricot.proxied_ldap_entry import (
    LDAPEntryList,
    MicrosoftEntraLDAPEntry,
    ProxiedLDAPEntry,
)


@implementer(IConnectedLDAPEntry)
class OAuthLookupTree:
    oauth_client: OAuthClient

    def __init__(self) -> None:
        # Create a root node for the tree
        root_dn = "DC=" + self.oauth_client.domain().replace(".", ",DC=")
        self.root = self.build_root(
            dn=root_dn, attributes={"objectClass": ["dcObject"]}
        )
        # Add OUs for users and groups
        groups_ou = self.root.add_child(
            "OU=groups", {"ou": ["groups"], "objectClass": ["organizationalUnit"]}
        )
        users_ou = self.root.add_child(
            "OU=users", {"ou": ["users"], "objectClass": ["organizationalUnit"]}
        )
        # Add groups to the groups OU
        for group_attrs in self.oauth_client.groups():
            groups_ou.add_child(f"CN={group_attrs['name'][0]}", group_attrs)
        # Add users to the users OU
        for user_attrs in self.oauth_client.users():
            users_ou.add_child(f"CN={user_attrs['name'][0]}", user_attrs)

    def build_root(self, dn: str, attributes: LDAPEntryList) -> ProxiedLDAPEntry:
        id((dn, attributes))  # ignore unused variables
        raise NotImplementedError

    def lookup(self, dn: DistinguishedName | str) -> defer.Deferred[ILDAPEntry]:
        """
        Lookup the referred to by dn.

        @return: A Deferred returning an ILDAPEntry, or failing with e.g.
        LDAPNoSuchObject.
        """
        if not isinstance(dn, DistinguishedName):
            dn = DistinguishedName(stringValue=dn)
        return self.root.lookup(dn)


class MicrosoftEntraLookupTree(OAuthLookupTree):
    def __init__(self, client_id: str, client_secret: str, tenant_id: str):
        self.oauth_client = MicrosoftEntraClient(
            client_id=client_id,
            client_secret=client_secret,
            tenant_id=tenant_id,
        )
        super().__init__()

    def build_root(self, dn: str, attributes: LDAPEntryList) -> ProxiedLDAPEntry:
        return MicrosoftEntraLDAPEntry(
            dn=dn, attributes=attributes, oauth_client=self.oauth_client
        )
