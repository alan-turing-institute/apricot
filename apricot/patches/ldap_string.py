"""Patch LDAPString to avoid TypeError when parsing LDAP filter strings."""

from typing import Any, Self

from ldaptor.protocols.pureldap import LDAPString

old_init = LDAPString.__init__


def patched_init(self: Self, *args: Any, **kwargs: Any) -> None:  # type: ignore[misc]
    """Patch LDAPString init to store its value as 'str' not 'bytes'."""
    old_init(self, *args, **kwargs)
    if isinstance(self.value, bytes):
        self.value = self.value.decode()


LDAPString.__init__ = patched_init
