from pydantic import BaseModel


class LDAPGroupOfNames(BaseModel):
    """
    A group with named members

    OID: 2.5.6.9
    Object class: Structural
    Parent: top
    Schema: rfc4519
    """

    cn: str
    description: str
    member: list[str]

    def names(self) -> list[str]:
        return ["groupOfNames"]
