from pydantic import BaseModel


class LdapInetUser(BaseModel):
    memberOf: list[str]  # noqa: N815
    uid: str
