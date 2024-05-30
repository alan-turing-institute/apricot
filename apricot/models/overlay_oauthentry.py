from __future__ import annotations

from .named_ldap_class import NamedLDAPClass


class OverlayOAuthEntry(NamedLDAPClass):
    """Abstraction for tracking an OAuth entry.

    OID: n/a
    Object class: Auxiliary
    Parent: top
    Schema: n/a
    """

    oauth_username: str | None = None
    oauth_id: str
