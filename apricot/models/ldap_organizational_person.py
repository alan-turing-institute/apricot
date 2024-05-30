from typing import Self

from .ldap_person import LDAPPerson


class LDAPOrganizationalPerson(LDAPPerson):
    """A person belonging to an organisation.

    OID: 2.5.6.7
    Object class: Structural
    Parent: person
    Schema: rfc4519
    """

    description: str

    def names(self: Self) -> list[str]:
        return [*super().names(), "organizationalPerson"]
