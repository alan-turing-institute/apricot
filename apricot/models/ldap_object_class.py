from __future__ import annotations

from typing import Self

from pydantic import BaseModel


class LDAPObjectClass(BaseModel):
    """An LDAP object-class that may have a name."""

    def names(self: Self) -> list[str]:
        """List of names for this LDAP object class."""
        return []
