from pydantic import BaseModel


class LdapInetOrgPerson(BaseModel):
    cn: str
    description: str
    displayName: str  # noqa: N815
    givenName: str  # noqa: N815
    sn: str
