from pydantic import BaseModel


class LdapGroupOfNames(BaseModel):
    cn: str
    description: str
    member: list[str]
