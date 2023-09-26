from ldaptor.interfaces import IConnectedLDAPEntry
from ldaptor.protocols.ldap.ldapserver import LDAPServer
from twisted.internet.interfaces import IAddress
from twisted.internet.protocol import Protocol, ServerFactory


class LDAPServerFactory(ServerFactory):
    protocol = LDAPServer

    def __init__(self, adaptor: IConnectedLDAPEntry):
        self.adaptor = adaptor

    def buildProtocol(self, addr: IAddress) -> Protocol:  # noqa: N802
        id(addr)  # ignore unused arguments
        proto = self.protocol()
        proto.factory = self.adaptor
        return proto
