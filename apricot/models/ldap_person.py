from pydantic import BaseModel


class LdapPerson(BaseModel):
    cn: str
    sn: str
