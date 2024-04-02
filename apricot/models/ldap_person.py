from pydantic import BaseModel


class LDAPPerson(BaseModel):
    """
    A named person

    OID: 2.5.6.6
    Object class: Structural
    Parent: top
    Schema: rfc4519
    """

    cn: str
    sn: str
