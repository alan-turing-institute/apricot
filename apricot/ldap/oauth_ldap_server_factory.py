from typing import Self

from twisted.internet.interfaces import IAddress
from twisted.internet.protocol import Protocol, ServerFactory

from apricot.oauth import OAuthClient, OAuthDataAdaptor

from .oauth_ldap_tree import OAuthLDAPTree
from .read_only_ldap_server import ReadOnlyLDAPServer


class OAuthLDAPServerFactory(ServerFactory):
    """A Twisted ServerFactory that provides an LDAP tree."""

    def __init__(
        self: Self,
        oauth_adaptor: OAuthDataAdaptor,
        oauth_client: OAuthClient,
        *,
        background_refresh: bool,
        refresh_interval: int,
    ) -> None:
        """Initialise an OAuthLDAPServerFactory.

        @param background_refresh: Whether to refresh the LDAP tree in the background rather than on access
        @param oauth_adaptor: An OAuth data adaptor used to construct the LDAP tree
        @param oauth_client: An OAuth client used to retrieve user and group data
        @param refresh_interval: Interval in seconds after which the tree must be refreshed
        """
        # Create an LDAP lookup tree
        self.adaptor = OAuthLDAPTree(
            oauth_adaptor,
            oauth_client,
            background_refresh=background_refresh,
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
        proto = ReadOnlyLDAPServer()
        proto.factory = self.adaptor
        return proto
