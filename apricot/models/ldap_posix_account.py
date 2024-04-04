import re

from pydantic import StringConstraints, validator
from typing_extensions import Annotated

from .named_ldap_class import NamedLDAPClass

ID_MIN = 2000
ID_MAX = 60000


class LDAPPosixAccount(NamedLDAPClass):
    """
    Abstraction of an account with POSIX attributes

    OID: 1.3.6.1.1.1.2.0
    Object class: Auxiliary
    Parent: top
    Schema: rfc2307bis
    """

    cn: str
    gidNumber: int  # noqa: N815
    homeDirectory: Annotated[  # noqa: N815
        str, StringConstraints(strip_whitespace=True, to_lower=True)
    ]
    uid: str
    uidNumber: int  # noqa: N815

    @validator("gidNumber")  # type: ignore[misc]
    @classmethod
    def validate_gid_number(cls, gid_number: int) -> int:
        """Avoid conflicts with existing users"""
        if not ID_MIN <= gid_number <= ID_MAX:
            msg = f"Must be in range {ID_MIN} to {ID_MAX}."
            raise ValueError(msg)
        return gid_number

    @validator("homeDirectory")  # type: ignore[misc]
    @classmethod
    def validate_home_directory(cls, home_directory: str) -> str:
        return re.sub(r"\s+", "-", home_directory)

    @validator("uidNumber")  # type: ignore[misc]
    @classmethod
    def validate_uid_number(cls, uid_number: int) -> int:
        """Avoid conflicts with existing users"""
        if not ID_MIN <= uid_number <= ID_MAX:
            msg = f"Must be in range {ID_MIN} to {ID_MAX}."
            raise ValueError(msg)
        return uid_number

    def names(self) -> list[str]:
        return ["posixAccount"]
