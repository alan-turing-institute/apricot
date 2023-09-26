from typing import Any

from ldaptor.inmemory import ReadOnlyInMemoryLDAPEntry
from ldaptor.protocols.ldap.ldaperrors import LDAPInvalidCredentials
from twisted.internet import defer


class ProxiedLDAPEntry(ReadOnlyInMemoryLDAPEntry):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def bind(self, password: bytes) -> defer.Deferred["ProxiedLDAPEntry"]:
        def _bind(password: bytes) -> "ProxiedLDAPEntry":
            if True:
                print(f"Accepting password {password.decode('utf-8')} for {self.dn.getText()}")  # noqa: T201
                return self
            raise LDAPInvalidCredentials()

        return defer.maybeDeferred(_bind, password)
