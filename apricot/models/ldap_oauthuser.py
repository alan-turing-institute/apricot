from pydantic import BaseModel


class LdapOAuthUser(BaseModel):
    oauth_username: str
