from __future__ import annotations

from .ldap_object_class import LDAPObjectClass


class LDAPPerson(LDAPObjectClass):
    """A named person.

    OID: 2.5.6.6
    Object class: Structural
    Parent: top
    Schema: rfc4519
    """

    _ldap_object_class_name: str = "person"

    cn: str
    sn: str
