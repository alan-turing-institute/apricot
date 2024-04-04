from .named_ldap_class import NamedLDAPClass


class LDAPPerson(NamedLDAPClass):
    """
    A named person

    OID: 2.5.6.6
    Object class: Structural
    Parent: top
    Schema: rfc4519
    """

    cn: str
    sn: str

    def names(self) -> list[str]:
        return ["person"]
