from .named_ldap_class import NamedLDAPClass


class OverlayOAuthEntry(NamedLDAPClass):
    """
    Abstraction of an OAuth entry

    OID: n/a
    Object class: Auxiliary
    Parent: top
    Schema: n/a
    """

    oauth_username: str
    oauth_id: str
