from pydantic import BaseModel


class LDAPOAuthUser(BaseModel):
    oauth_username: str
