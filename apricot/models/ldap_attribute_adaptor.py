from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self, Sequence

if TYPE_CHECKING:
    from apricot.models import LDAPObjectClass
    from apricot.typedefs import JSONDict, LDAPAttributeDict


class LDAPAttributeAdaptor:
    """A class to convert attributes into LDAP format."""

    def __init__(self: Self, attributes: dict[Any, Any]) -> None:
        """Initialise an LDAPAttributeAdaptor.

        Args:
            attributes: A dictionary of attributes to be converted into LDAP format
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

    @classmethod
    def from_attributes(
        cls: type[Self],
        input_dict: JSONDict,
        *,
        required_classes: Sequence[type[LDAPObjectClass]],
    ) -> LDAPAttributeAdaptor:
        """Construct an LDAPAttributeAdaptor from attributes and required classes.

        Args:
            input_dict: Dictionary of attributes
            required_classes: Sequence of required LDAP classes

        Returns:
            An LDAPAttributeAdaptor with these attributes
        """
        attributes = {"objectclass": ["top"]}
        for ldap_class in required_classes:
            model = ldap_class(**input_dict)
            attributes.update(model.model_dump())
            attributes["objectclass"] += model.names()
        return cls(attributes)

    def to_dict(self: Self) -> LDAPAttributeDict:
        """Convert the attributes to an LDAPAttributeDict.

        Returns:
            Attributes as an LDAPAttributeDict
        """
        return self.attributes
