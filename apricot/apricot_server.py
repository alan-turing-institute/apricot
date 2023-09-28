import sys
from typing import Any, cast

from twisted.internet import reactor
from twisted.internet.endpoints import serverFromString
from twisted.internet.interfaces import IReactorCore, IStreamServerEndpoint
from twisted.python import log

from apricot.ldap import OAuthLDAPServerFactory
from apricot.oauth import MicrosoftEntraClient, OAuthBackend


class ApricotServer:
    def __init__(
        self,
        backend: OAuthBackend,
        client_id: str,
        client_secret: str,
        port: int,
        **kwargs: Any,
    ) -> None:
        # Log to stdout
        log.startLogging(sys.stdout)

        # Initialize the appropriate OAuth client
        oauth_client = None
        if backend == OAuthBackend.MICROSOFT_ENTRA:
            oauth_client = MicrosoftEntraClient(
                client_id=client_id,
                client_secret=client_secret,
                tenant_id=kwargs["entra_tenant_id"],
            )
        if not oauth_client:
            msg = f"Could not construct an OAuth client for the '{backend}' backend."
            raise ValueError(msg)

        # Create an LDAPServerFactory
        factory = OAuthLDAPServerFactory(oauth_client)

        # Attach a listening endpoint
        endpoint: IStreamServerEndpoint = serverFromString(reactor, f"tcp:{port}")
        endpoint.listen(factory)

        # Load the Twisted reactor
        self.reactor = cast(IReactorCore, reactor)

    def run(self) -> None:
        """Start the Twisted reactor"""
        self.reactor.run()
