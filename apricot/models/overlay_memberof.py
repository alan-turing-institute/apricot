from __future__ import annotations

from .named_ldap_class import NamedLDAPClass


class OverlayMemberOf(NamedLDAPClass):
    """Abstraction for tracking the groups that an individual belongs to.

    OID: n/a
    Object class: Auxiliary
    Parent: top
    Schema: rfc2307bis
    """

    memberOf: list[str]  # noqa: N815
