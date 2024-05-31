from __future__ import annotations

from .ldap_object_class import LDAPObjectClass


class OverlayMemberOf(LDAPObjectClass):
    """Abstraction for tracking the groups that an individual belongs to.

    OID: n/a
    Object class: Auxiliary
    Parent: top
    Schema: rfc2307bis
    """

    memberOf: list[str]  # noqa: N815
