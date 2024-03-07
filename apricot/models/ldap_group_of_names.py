from pydantic import BaseModel


class LDAPGroupOfNames(BaseModel):
    cn: str
    description: str
    member: list[str]
