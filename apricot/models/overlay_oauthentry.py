from __future__ import annotations

from .ldap_object_class import LDAPObjectClass


class OverlayOAuthEntry(LDAPObjectClass):
    """Abstraction for tracking an OAuth entry.

    OID: n/a
    Object class: Auxiliary
    Parent: top
    Schema: n/a
    """

    oauth_username: str | None = None
    oauth_id: str
