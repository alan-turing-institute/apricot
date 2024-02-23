from pydantic import BaseModel, validator

ID_MIN = 2000
ID_MAX = 4294967295


class LdapPosixGroup(BaseModel):
    description: str
    gidNumber: int  # noqa: N815
    memberUid: list[str]  # noqa: N815

    @validator("gidNumber")
    @classmethod
    def validate_gid_number(cls, gid_number: int) -> int:
        """Avoid conflicts with existing groups"""
        if not ID_MIN <= gid_number <= ID_MAX:
            msg = f"Must be in range {ID_MIN} to {ID_MAX}."
            raise ValueError(msg)
        return gid_number
