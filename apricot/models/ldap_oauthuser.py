from pydantic import BaseModel


class LDAPOAuthUser(BaseModel):
    """
    Abstraction of an OAuth user account

    OID: n/a
    Object class: Auxiliary
    Parent: top
    Schema: n/a
    """

    oauth_username: str
