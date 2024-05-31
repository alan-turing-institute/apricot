from __future__ import annotations

from .ldap_person import LDAPPerson


class LDAPOrganizationalPerson(LDAPPerson):
    """A person belonging to an organisation.

    OID: 2.5.6.7
    Object class: Structural
    Parent: person
    Schema: rfc4519
    """

    _ldap_object_class_name: str = "organizationalPerson"

    description: str
