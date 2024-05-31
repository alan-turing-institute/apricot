from __future__ import annotations

from .ldap_object_class import LDAPObjectClass


class LDAPGroupOfNames(LDAPObjectClass):
    """A group with named members.

    OID: 2.5.6.9
    Object class: Structural
    Parent: top
    Schema: rfc4519
    """

    _ldap_object_class_name: str = "groupOfNames"

    cn: str
    description: str
    member: list[str]
