from typing import Self

from pydantic import BaseModel


class NamedLDAPClass(BaseModel):
    """An LDAP class that has a name."""

    def names(self: Self) -> list[str]:
        """List of names for this LDAP object class."""
        return []
