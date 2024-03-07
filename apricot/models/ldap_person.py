from pydantic import BaseModel


class LDAPPerson(BaseModel):
    cn: str
    sn: str
