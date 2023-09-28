from abc import ABC, abstractmethod

from ldaptor.interfaces import IConnectedLDAPEntry, ILDAPEntry
from ldaptor.protocols.ldap.distinguishedname import DistinguishedName
from twisted.internet import defer
from zope.interface import implementer

from apricot.oauth_clients import OAuthClient
from apricot.proxied_ldap_entry import (
    LDAPEntryList,
    ProxiedLDAPEntry,
)


@implementer(IConnectedLDAPEntry)
class OAuthLDAPTree(ABC):
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

    @abstractmethod
    def build_root(self, dn: str, attributes: LDAPEntryList) -> ProxiedLDAPEntry:
        pass

    def lookup(self, dn: DistinguishedName | str) -> defer.Deferred[ILDAPEntry]:
        """
        Lookup the referred to by dn.

        @return: A Deferred returning an ILDAPEntry, or failing with e.g.
        LDAPNoSuchObject.
        """
        if not isinstance(dn, DistinguishedName):
            dn = DistinguishedName(stringValue=dn)
        return self.root.lookup(dn)
