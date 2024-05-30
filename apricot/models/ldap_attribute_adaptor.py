from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from apricot.types import LDAPAttributeDict


class LDAPAttributeAdaptor:
    """A class to convert attributes into LDAP format."""

    def __init__(self: Self, attributes: dict[Any, Any]) -> None:
        """Initialise an LDAPAttributeAdaptor.

        @param attributes: A dictionary of attributes to be converted into str: list[str]
        """
        self.attributes = {
            str(k): list(map(str, v)) if isinstance(v, list) else [str(v)]
            for k, v in attributes.items()
            if v is not None
        }

    @property
    def cn(self: Self) -> str:
        """Return CN for this set of LDAP attributes."""
        return self.attributes["cn"][0]

    def to_dict(self: Self) -> LDAPAttributeDict:
        """Convert the attributes to an LDAPAttributeDict."""
        return self.attributes
