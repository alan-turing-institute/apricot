from twisted.internet.interfaces import IAddress
from twisted.internet.protocol import Protocol, ServerFactory

from apricot.oauth import OAuthClient

from .oauth_ldap_tree import OAuthLDAPTree
from .read_only_ldap_server import ReadOnlyLDAPServer


class OAuthLDAPServerFactory(ServerFactory):
    def __init__(self, domain: str, oauth_client: OAuthClient, enable_group_of_groups: bool):
        """
        Initialise an LDAPServerFactory

        @param oauth_client: An OAuth client used to construct the LDAP tree
        """
        # Create an LDAP lookup tree
        self.adaptor = OAuthLDAPTree(domain, oauth_client, enable_group_of_groups)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__} using adaptor {self.adaptor}"

    def buildProtocol(self, addr: IAddress) -> Protocol:  # noqa: N802
        """
        Create an LDAPServer instance.

        This instance will use self.adaptor to produce LDAP entries.

        @param addr: an object implementing L{IAddress}
        """
        id(addr)  # ignore unused arguments
        proto = ReadOnlyLDAPServer(debug=self.adaptor.debug)
        proto.factory = self.adaptor
        return proto
