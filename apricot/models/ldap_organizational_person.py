from pydantic import BaseModel


class LDAPOrganizationalPerson(BaseModel):
    """
    A person belonging to an organisation

    OID: 2.5.6.7
    Object class: Structural
    Parent: person
    Schema: rfc4519
    """

    description: str
