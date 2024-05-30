from typing import Self

from pydantic import BaseModel


class NamedLDAPClass(BaseModel):
    def names(self: Self) -> list[str]:
        """List of names for this LDAP object class"""
        return []
