from ldaptor.inmemory import ReadOnlyInMemoryLDAPEntry
from ldaptor.protocols.ldap.distinguishedname import (
    DistinguishedName,
    RelativeDistinguishedName,
)
from ldaptor.protocols.ldap.ldaperrors import (
    LDAPEntryAlreadyExists,
    LDAPInvalidCredentials,
)
from twisted.internet import defer
from twisted.python import log

from apricot.oauth_clients import LDAPAttributeDict, OAuthClient


class ProxiedLDAPEntry(ReadOnlyInMemoryLDAPEntry):
    dn: DistinguishedName
    attributes: LDAPAttributeDict

    def __init__(
        self,
        dn: DistinguishedName | str,
        attributes: LDAPAttributeDict,
        oauth_client: OAuthClient | None = None,
    ) -> None:
        self.oauth_client_ = oauth_client
        if not isinstance(dn, DistinguishedName):
            dn = DistinguishedName(stringValue=dn)
        super().__init__(dn, attributes)

    def __str__(self) -> str:
        output = self.toWire().decode("utf-8")
        for child in self._children.values():
            try:
                output += f"\n- {child!s}"
            except TypeError:
                pass
        return output

    @property
    def oauth_client(self) -> OAuthClient:
        if not self.oauth_client_:
            if hasattr(self._parent, "oauth_client"):
                self.oauth_client_ = self._parent.oauth_client
        if not isinstance(self.oauth_client_, OAuthClient):
            msg = f"OAuthClient is of incorrect type {type(self.oauth_client_)}"
            raise TypeError(msg)
        return self.oauth_client_

    @property
    def username(self) -> str:
        username = self.dn.split()[0].getText().split("CN=")[1]
        domain = self.dn.getDomainName()
        return f"{username}@{domain}"

    def add_child(
        self, rdn: RelativeDistinguishedName | str, attributes: LDAPAttributeDict
    ) -> "ProxiedLDAPEntry | None":
        if isinstance(rdn, str):
            rdn = RelativeDistinguishedName(stringValue=rdn)
        try:
            return self.addChild(rdn, attributes)
        except LDAPEntryAlreadyExists:
            log.msg(f"Refusing to add child '{rdn.getText()}' as it already exists.")
        return None

    def bind(self, password: bytes) -> defer.Deferred["ProxiedLDAPEntry"]:
        def _bind(password: bytes) -> "ProxiedLDAPEntry":
            s_password = password.decode("utf-8")
            if self.oauth_client.verify(username=self.username, password=s_password):
                return self
            msg = f"Invalid password for user '{self.username}'."
            raise LDAPInvalidCredentials(msg)

        return defer.maybeDeferred(_bind, password)
