import time

from ldaptor.interfaces import IConnectedLDAPEntry, ILDAPEntry
from ldaptor.protocols.ldap.distinguishedname import DistinguishedName
from twisted.internet import defer
from twisted.python import log
from zope.interface import implementer

from apricot.ldap.oauth_ldap_entry import OAuthLDAPEntry
from apricot.oauth import OAuthClient


@implementer(IConnectedLDAPEntry)
class OAuthLDAPTree:
    oauth_client: OAuthClient

    def __init__(self, oauth_client: OAuthClient, refresh_interval: int = 60) -> None:
        """
        Initialise an OAuthLDAPTree

        @param oauth_client: An OAuth client used to construct the LDAP tree
        @param refresh_interval: Interval in seconds after which the tree must be refreshed
        """
        self.debug = oauth_client.debug
        self.last_update = time.monotonic()
        self.oauth_client: OAuthClient = oauth_client
        self.refresh_interval = refresh_interval
        self.root_: OAuthLDAPEntry | None = None

    @property
    def dn(self) -> DistinguishedName:
        return self.root.dn

    @property
    def root(self) -> OAuthLDAPEntry:
        """
        Lazy-load the LDAP tree on request

        @return: An OAuthLDAPEntry for the tree
        """
        if (
            not self.root_
            or (time.monotonic() - self.last_update) > self.refresh_interval
        ):
            log.msg("Rebuilding LDAP tree from OAuth data.")
            # Create a root node for the tree
            self.root_ = OAuthLDAPEntry(
                dn=self.oauth_client.root_dn,
                attributes={"objectClass": ["dcObject"]},
                oauth_client=self.oauth_client,
            )
            # Add OUs for users and groups
            groups_ou = self.root_.add_child(
                "OU=groups", {"ou": ["groups"], "objectClass": ["organizationalUnit"]}
            )
            users_ou = self.root_.add_child(
                "OU=users", {"ou": ["users"], "objectClass": ["organizationalUnit"]}
            )
            # Add groups to the groups OU
            if self.debug:
                log.msg("Adding groups to the LDAP tree.")
            for group_attrs in self.oauth_client.groups():
                groups_ou.add_child(f"CN={group_attrs.cn}", group_attrs.to_dict())
            # Add users to the users OU
            if self.debug:
                log.msg("Adding users to the LDAP tree.")
            for user_attrs in self.oauth_client.users():
                users_ou.add_child(f"CN={user_attrs.cn}", user_attrs.to_dict())
            # Set last updated time
            log.msg("Finished building LDAP tree.")
            self.last_update = time.monotonic()
        return self.root_

    def __repr__(self) -> str:
        return f"{self.__class__.__name__} with backend {self.oauth_client.__class__.__name__}"

    def lookup(self, dn: DistinguishedName | str) -> defer.Deferred[ILDAPEntry]:
        """
        Lookup the referred to by dn.

        @return: A Deferred returning an ILDAPEntry.

        @raises: LDAPNoSuchObject.
        """
        if not isinstance(dn, DistinguishedName):
            dn = DistinguishedName(stringValue=dn)
        if self.debug:
            log.msg(f"Starting an LDAP lookup for '{dn.getText()}'.")
        return self.root.lookup(dn)
