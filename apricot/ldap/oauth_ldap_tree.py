from __future__ import annotations

import time
from typing import TYPE_CHECKING, Self

from ldaptor.interfaces import IConnectedLDAPEntry, ILDAPEntry
from ldaptor.protocols.ldap.distinguishedname import DistinguishedName
from twisted.logger import Logger
from zope.interface import implementer

from apricot.ldap.oauth_ldap_entry import OAuthLDAPEntry

if TYPE_CHECKING:
    from twisted.internet import defer
    from twisted.python.failure import Failure

    from apricot.oauth import OAuthClient, OAuthDataAdaptor


@implementer(IConnectedLDAPEntry)
class OAuthLDAPTree:
    """An LDAP tree that represents a view of an OAuth directory."""

    def __init__(
        self: Self,
        oauth_adaptor: OAuthDataAdaptor,
        oauth_client: OAuthClient,
        *,
        background_refresh: bool,
        refresh_interval: int,
    ) -> None:
        """Initialise an OAuthLDAPTree.

        Args:
            background_refresh: Whether to refresh the LDAP tree in the background
                rather than on access
            oauth_adaptor: An OAuth data adaptor used to construct the LDAP tree
            oauth_client: An OAuth client used to retrieve user and group data
            refresh_interval: Interval in seconds after which the tree must be refreshed
        """
        self.background_refresh = background_refresh
        self.last_update = time.monotonic()
        self.logger = Logger()
        self.oauth_adaptor = oauth_adaptor
        self.oauth_client = oauth_client
        self.refresh_interval = refresh_interval
        self.root_: OAuthLDAPEntry | None = None

    @property
    def dn(self: Self) -> DistinguishedName:
        """The distinguished name of this tree.

        Returns:
            The distinguished name of the tree root.
        """
        return self.root.dn

    @property
    def root(self: Self) -> OAuthLDAPEntry:
        """Lazy-load the LDAP tree on request.

        Returns:
            An OAuthLDAPEntry for the tree

        Raises:
            ValueError: if the tree could not be loaded.
        """
        if not self.background_refresh:
            self.refresh()
        if not self.root_:
            msg = "LDAP tree could not be loaded"
            raise ValueError(msg)
        return self.root_

    def __repr__(self: Self) -> str:
        """Generate string representation of OAuthLDAPTree.

        Returns:
            A string representation of OAuthLDAPTree.
        """
        return f"{self.__class__.__name__} with backend {self.oauth_client.__class__.__name__}"  # noqa: E501

    def lookup(self: Self, dn: DistinguishedName | str) -> defer.Deferred[ILDAPEntry]:
        """Lookup a DistinguishedName in the LDAP tree.

        Args:
            dn: A distinguished name to lookup.

        Returns:
            The result of the lookup as a deferred LDAP entry.
        """

        def result_callback(ldap_entry: OAuthLDAPEntry | None) -> OAuthLDAPEntry | None:
            if ldap_entry:
                self.logger.debug(
                    "LDAP lookup succeeded: found {dn}",
                    dn=ldap_entry.dn.getText(),
                )
            return ldap_entry

        def failure_callback(failure: Failure) -> Failure:
            self.logger.debug(
                "LDAP lookup failed: {error}",
                error=failure.getErrorMessage(),
            )
            return failure

        # Construct a complete DN
        if not isinstance(dn, DistinguishedName):
            dn = DistinguishedName(stringValue=dn)
        self.logger.info("Starting an LDAP lookup for '{dn}'.", dn=dn.getText())

        # Attach debug callbacks to the lookup and return
        return (
            self.root.lookup(dn)
            .addErrback(failure_callback)
            .addCallback(result_callback)
        )

    def refresh(self: Self) -> None:
        """Refresh the LDAP tree."""
        if (
            not self.root_
            or (time.monotonic() - self.last_update) > self.refresh_interval
        ):
            # Update users and groups from the OAuth server
            self.logger.info("Retrieving OAuth data.")
            oauth_groups, oauth_users = self.oauth_adaptor.retrieve_all()

            # Create a root node for the tree
            self.logger.info("Rebuilding LDAP tree.")
            self.root_ = OAuthLDAPEntry(
                dn=self.oauth_adaptor.root_dn,
                attributes={"objectClass": ["dcObject"]},
                oauth_client=self.oauth_client,
            )

            # Add OUs for users and groups
            groups_ou = self.root_.add_child(
                "OU=groups",
                {"ou": ["groups"], "objectClass": ["organizationalUnit"]},
            )
            users_ou = self.root_.add_child(
                "OU=users",
                {"ou": ["users"], "objectClass": ["organizationalUnit"]},
            )

            # Add groups to the groups OU
            self.logger.debug(
                "Attempting to add {n_groups} groups to the LDAP tree.",
                n_groups=len(oauth_groups),
            )
            for group_attrs in oauth_groups:
                groups_ou.add_child(f"CN={group_attrs.cn}", group_attrs.to_dict())
            ldap_groups = groups_ou.list_children()
            self.logger.info(
                "There are {n_groups} groups in the LDAP tree.",
                n_groups=len(ldap_groups),
            )
            for ldap_group in ldap_groups:
                self.logger.debug(
                    "... {ldap_group}",
                    ldap_group=ldap_group.dn.getText(),
                )

            # Add users to the users OU
            self.logger.debug(
                "Attempting to add {n_users} users to the LDAP tree.",
                n_users=len(oauth_users),
            )
            for user_attrs in oauth_users:
                users_ou.add_child(f"CN={user_attrs.cn}", user_attrs.to_dict())
            ldap_users = users_ou.list_children()
            self.logger.info(
                "There are {n_users} users in the LDAP tree.",
                n_users=len(ldap_users),
            )
            for ldap_user in ldap_users:
                self.logger.debug("... {ldap_user}", ldap_user=ldap_user.dn.getText())

            # Set last updated time
            self.logger.info("Finished building LDAP tree.")
            self.last_update = time.monotonic()
