from __future__ import annotations

from typing import Self

from pydantic import BaseModel


class LDAPObjectClass(BaseModel):
    """An LDAP object-class that may have a name."""

    @classmethod
    def names(cls: type[Self]) -> list[str]:
        """List of object-class names for this LDAP object-class.

        We iterate through the parent classes in MRO order, getting an
        `_ldap_object_class_name` from each class that has one. We then sort these
        before returning a list of names.
        """
        return sorted(
            [
                cls_._ldap_object_class_name.default
                for cls_ in cls.__mro__
                if hasattr(cls_, "_ldap_object_class_name")
            ],
        )
