from typing import Self

from twisted.internet.interfaces import IAddress
from twisted.internet.protocol import Protocol, ServerFactory

from apricot.oauth import OAuthClient

from .oauth_ldap_tree import OAuthLDAPTree
from .read_only_ldap_server import ReadOnlyLDAPServer


class OAuthLDAPServerFactory(ServerFactory):
    """A Twisted ServerFactory that provides an LDAP tree."""

    def __init__(
        self: Self,
        domain: str,
        oauth_client: OAuthClient,
        *,
        background_refresh: bool,
        enable_mirrored_groups: bool,
        refresh_interval: int,
    ) -> None:
        """Initialise an OAuthLDAPServerFactory.

        @param background_refresh: Whether to refresh the LDAP tree in the background rather than on access
        @param domain: The root domain of the LDAP tree
        @param enable_mirrored_groups: Create a mirrored LDAP group-of-groups for each group-of-users
        @param oauth_client: An OAuth client used to construct the LDAP tree
        @param refresh_interval: Interval in seconds after which the tree must be refreshed
        """
        # Create an LDAP lookup tree
        self.adaptor = OAuthLDAPTree(
            domain,
            oauth_client,
            background_refresh=background_refresh,
            enable_mirrored_groups=enable_mirrored_groups,
            refresh_interval=refresh_interval,
        )

    def __repr__(self: Self) -> str:
        return f"{self.__class__.__name__} using adaptor {self.adaptor}"

    def buildProtocol(self: Self, addr: IAddress) -> Protocol:  # noqa: N802
        """Create an LDAPServer instance.

        This instance will use self.adaptor to produce LDAP entries.

        @param addr: an object implementing L{IAddress}
        """
        id(addr)  # ignore unused arguments
        proto = ReadOnlyLDAPServer(debug=self.adaptor.debug)
        proto.factory = self.adaptor
        return proto
