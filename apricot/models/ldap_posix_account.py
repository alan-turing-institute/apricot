from __future__ import annotations

import re
from typing import Self

from pydantic import StringConstraints, validator
from typing_extensions import Annotated

from .ldap_object_class import LDAPObjectClass

ID_MIN = 2000
ID_MAX = 60000


class LDAPPosixAccount(LDAPObjectClass):
    """Abstraction of an account with POSIX attributes.

    OID: 1.3.6.1.1.1.2.0
    Object class: Auxiliary
    Parent: top
    Schema: rfc2307bis
    """

    _ldap_object_class_name: str = "posixAccount"

    cn: str
    gidNumber: int  # noqa: N815
    homeDirectory: Annotated[  # noqa: N815
        str,
        StringConstraints(strip_whitespace=True, to_lower=True),
    ]
    uid: str
    uidNumber: int  # noqa: N815

    @validator("gidNumber")  # type: ignore[misc]
    @classmethod
    def validate_gid_number(cls: type[Self], gid_number: int) -> int:
        """Avoid conflicts with existing users.

        Args:
            gid_number: Proposed gid_number

        Returns:
            The gid_number if valid.

        Raises:
            ValueError: if the gid_number is not in an acceptable range
        """
        if not ID_MIN <= gid_number <= ID_MAX:
            msg = f"Must be in range {ID_MIN} to {ID_MAX}."
            raise ValueError(msg)
        return gid_number

    @validator("homeDirectory")  # type: ignore[misc]
    @classmethod
    def validate_home_directory(cls: type[Self], home_directory: str) -> str:
        """Validate home directory path by removing whitespace.

        Returns:
            The sanitised home directory path.
        """
        return re.sub(r"\s+", "-", home_directory)

    @validator("uidNumber")  # type: ignore[misc]
    @classmethod
    def validate_uid_number(cls: type[Self], uid_number: int) -> int:
        """Avoid conflicts with existing users.

        Args:
            uid_number: Proposed uid_number

        Returns:
            The uid_number if valid.

        Raises:
            ValueError: if the uid_number is not in an acceptable range
        """
        if not ID_MIN <= uid_number <= ID_MAX:
            msg = f"Must be in range {ID_MIN} to {ID_MAX}."
            raise ValueError(msg)
        return uid_number
