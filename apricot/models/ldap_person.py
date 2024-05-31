from __future__ import annotations

from typing import Self

from .ldap_object_class import LDAPObjectClass


class LDAPPerson(LDAPObjectClass):
    """A named person.

    OID: 2.5.6.6
    Object class: Structural
    Parent: top
    Schema: rfc4519
    """

    cn: str
    sn: str

    def names(self: Self) -> list[str]:
        return ["person"]
