import sys
from typing import Any, cast

from twisted.internet import reactor
from twisted.internet.endpoints import serverFromString
from twisted.internet.interfaces import IReactorCore, IStreamServerEndpoint
from twisted.python import log

from apricot.ldap import OAuthLDAPServerFactory
from apricot.oauth import OAuthBackend, OAuthClientMap


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
        try:
            oauth_client = OAuthClientMap[backend](
                client_id=client_id, client_secret=client_secret, **kwargs
            )
        except Exception as exc:
            msg = f"Could not construct an OAuth client for the '{backend}' backend."
            raise ValueError(msg) from exc

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
