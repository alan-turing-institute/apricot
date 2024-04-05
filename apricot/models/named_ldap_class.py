from pydantic import BaseModel


class NamedLDAPClass(BaseModel):
    def names(self) -> list[str]:
        """List of names for this LDAP object class"""
        return []
