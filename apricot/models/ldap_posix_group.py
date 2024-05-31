from __future__ import annotations

from typing import Self

from pydantic import validator

from .ldap_object_class import LDAPObjectClass

ID_MIN = 2000
ID_MAX = 4294967295


class LDAPPosixGroup(LDAPObjectClass):
    """Abstraction of a group of accounts.

    OID: 1.3.6.1.1.1.2.2
    Object class: Auxiliary
    Parent: top
    Schema: rfc2307bis
    """

    _ldap_object_class_name: str = "posixGroup"

    description: str
    gidNumber: int  # noqa: N815
    memberUid: list[str]  # noqa: N815

    @validator("gidNumber")  # type: ignore[misc]
    @classmethod
    def validate_gid_number(cls: type[Self], gid_number: int) -> int:
        """Avoid conflicts with existing groups."""
        if not ID_MIN <= gid_number <= ID_MAX:
            msg = f"Must be in range {ID_MIN} to {ID_MAX}."
            raise ValueError(msg)
        return gid_number
