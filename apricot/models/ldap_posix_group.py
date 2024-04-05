from pydantic import validator

from .named_ldap_class import NamedLDAPClass

ID_MIN = 2000
ID_MAX = 4294967295


class LDAPPosixGroup(NamedLDAPClass):
    """
    Abstraction of a group of accounts

    OID: 1.3.6.1.1.1.2.2
    Object class: Auxiliary
    Parent: top
    Schema: rfc2307bis
    """

    description: str
    gidNumber: int  # noqa: N815
    memberUid: list[str]  # noqa: N815

    @validator("gidNumber")  # type: ignore[misc]
    @classmethod
    def validate_gid_number(cls, gid_number: int) -> int:
        """Avoid conflicts with existing groups"""
        if not ID_MIN <= gid_number <= ID_MAX:
            msg = f"Must be in range {ID_MIN} to {ID_MAX}."
            raise ValueError(msg)
        return gid_number

    def names(self) -> list[str]:
        return ["posixGroup"]
