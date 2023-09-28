import sys
from typing import Any, cast

from twisted.internet import reactor
from twisted.internet.endpoints import serverFromString
from twisted.internet.interfaces import IReactorCore, IStreamServerEndpoint
from twisted.python import log

from apricot.ldap_server_factory import LDAPServerFactory
from apricot.ldap_tree import MicrosoftEntraLDAPTree
from apricot.oauth_clients import OAuthBackend


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

        # Initialize the LDAP lookup tree
        if backend == OAuthBackend.MICROSOFT_ENTRA:
            tree = MicrosoftEntraLDAPTree(
                client_id=client_id,
                client_secret=client_secret,
                tenant_id=kwargs["tenant_id"],
            )
        else:
            msg = f"Could not construct a lookup tree for the '{backend}' backend."
            raise ValueError(msg)

        # Create an LDAPServerFactory
        factory = LDAPServerFactory(tree)

        # Attach a listening endpoint
        endpoint: IStreamServerEndpoint = serverFromString(reactor, f"tcp:{port}")
        endpoint.listen(factory)

        # Load the Twisted reactor
        self.reactor = cast(IReactorCore, reactor)

    def run(self) -> None:
        """Start the Twisted reactor"""
        self.reactor.run()
