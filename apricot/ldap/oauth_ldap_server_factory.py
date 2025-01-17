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
        allow_anonymous_binds: bool,
        background_refresh: bool,
        refresh_interval: int,
    ) -> None:
        """Initialise an OAuthLDAPServerFactory.

        Args:
            allow_anonymous_binds: Whether to allow anonymous LDAP binds
            background_refresh: Whether to refresh the LDAP tree in the background
                rather than on access
            oauth_adaptor: An OAuth data adaptor used to construct the LDAP tree
            oauth_client: An OAuth client used to retrieve user and group data
            refresh_interval: Interval in seconds after which the tree must be refreshed
        """
        # Create an LDAP lookup tree
        self.adaptor = OAuthLDAPTree(
            oauth_adaptor,
            oauth_client,
            background_refresh=background_refresh,
            refresh_interval=refresh_interval,
        )
        self.allow_anonymous_binds = allow_anonymous_binds

    def __repr__(self: Self) -> str:
        """Generate string representation of OAuthLDAPServerFactory.

        Returns:
            A string representation of OAuthLDAPServerFactory.
        """
        return f"{self.__class__.__name__} using adaptor {self.adaptor}"

    def buildProtocol(self: Self, addr: IAddress) -> Protocol:  # noqa: N802
        """Create an LDAPServer instance.

        This instance will use self.adaptor to produce LDAP entries.

        Args:
            addr: an object implementing L{IAddress}

        Returns:
            The ReadOnlyLDAPServer with an attached OAuth adaptor.
        """
        id(addr)  # ignore unused arguments
        proto = ReadOnlyLDAPServer(allow_anonymous_binds=self.allow_anonymous_binds)
        proto.factory = self.adaptor
        return proto
