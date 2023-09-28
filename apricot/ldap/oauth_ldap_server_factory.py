from ldaptor.protocols.ldap.ldapserver import LDAPServer
from twisted.internet.interfaces import IAddress
from twisted.internet.protocol import Protocol, ServerFactory

from apricot.oauth import OAuthClient

from .oauth_ldap_tree import OAuthLDAPTree


class OAuthLDAPServerFactory(ServerFactory):
    protocol = LDAPServer

    def __init__(self, oauth_client: OAuthClient):
        """
        Initialise an LDAPServerFactory

        @param oauth_client: An OAuth client used to construct the LDAP tree
        """
        # Create an LDAP lookup tree
        self.adaptor = OAuthLDAPTree(oauth_client)

    def buildProtocol(self, addr: IAddress) -> Protocol:  # noqa: N802
        """
        Create an LDAPServer instance.

        This instance will use self.adaptor to produce LDAP entries.

        @param addr: an object implementing L{IAddress}
        """
        id(addr)  # ignore unused arguments
        proto = self.protocol()
        proto.factory = self.adaptor
        return proto
