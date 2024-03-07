from pydantic import BaseModel


class LDAPInetUser(BaseModel):
    memberOf: list[str]  # noqa: N815
    uid: str
