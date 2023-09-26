import sys
from typing import cast

from twisted.internet import reactor
from twisted.internet.endpoints import serverFromString
from twisted.internet.interfaces import IReactorCore, IStreamServerEndpoint
from twisted.python import log

from .ldap_lookup_tree import LDAPLookupTree
from .ldap_server_factory import LDAPServerFactory

class ApricotServer():
    def __init__(self, port: int) -> None:
        # Log to stdout
        log.startLogging(sys.stdout)

        # Initialize the LDAP lookup tree
        tree = LDAPLookupTree()

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
