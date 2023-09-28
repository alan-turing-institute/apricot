from ldaptor.interfaces import IConnectedLDAPEntry, ILDAPEntry
from ldaptor.protocols.ldap.distinguishedname import DistinguishedName
from twisted.internet import defer
from zope.interface import implementer

from apricot.ldap.oauth_ldap_entry import OAuthLDAPEntry
from apricot.oauth import LDAPAttributeDict, OAuthClient


@implementer(IConnectedLDAPEntry)
class OAuthLDAPTree:
    oauth_client: OAuthClient

    def __init__(self, oauth_client: OAuthClient) -> None:
        """
        Initialise an OAuthLDAPTree

        @param oauth_client: An OAuth client used to construct the LDAP tree
        """
        self.oauth_client = oauth_client

        # Create a root node for the tree
        self.root = self.build_root(
            dn=self.oauth_client.root_dn, attributes={"objectClass": ["dcObject"]}
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

    def build_root(self, dn: str, attributes: LDAPAttributeDict) -> OAuthLDAPEntry:
        """
        Construct the root of the LDAP tree

        @param dn: Distinguished Name of the object
        @param attributes: Attributes of the object.

        @return: An OAuthLDAPEntry
        """
        return OAuthLDAPEntry(
            dn=dn, attributes=attributes, oauth_client=self.oauth_client
        )

    def lookup(self, dn: DistinguishedName | str) -> defer.Deferred[ILDAPEntry]:
        """
        Lookup the referred to by dn.

        @return: A Deferred returning an ILDAPEntry.

        @raises: LDAPNoSuchObject.
        """
        if not isinstance(dn, DistinguishedName):
            dn = DistinguishedName(stringValue=dn)
        return self.root.lookup(dn)
