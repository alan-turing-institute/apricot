from typing import Any, Self

from apricot.types import LDAPAttributeDict


class LDAPAttributeAdaptor:
    def __init__(self: Self, attributes: dict[Any, Any]) -> None:
        self.attributes = {
            str(k): list(map(str, v)) if isinstance(v, list) else [str(v)]
            for k, v in attributes.items()
            if v is not None
        }

    @property
    def cn(self: Self) -> str:
        """Return CN for this set of LDAP attributes"""
        return self.attributes["cn"][0]

    def to_dict(self: Self) -> LDAPAttributeDict:
        """Convert the attributes to an LDAPAttributeDict"""
        return self.attributes
