from __future__ import annotations

from typing import Self

from .named_ldap_class import NamedLDAPClass


class LDAPGroupOfNames(NamedLDAPClass):
    """A group with named members.

    OID: 2.5.6.9
    Object class: Structural
    Parent: top
    Schema: rfc4519
    """

    cn: str
    description: str
    member: list[str]

    def names(self: Self) -> list[str]:
        return ["groupOfNames"]
