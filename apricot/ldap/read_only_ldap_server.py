from typing import Callable

from ldaptor.interfaces import ILDAPEntry
from ldaptor.protocols.ldap.ldaperrors import LDAPProtocolError
from ldaptor.protocols.ldap.ldapserver import LDAPServer
from ldaptor.protocols.pureldap import (
    LDAPBindRequest,
    LDAPControl,
    LDAPSearchResultDone,
    LDAPSearchResultEntry,
)
from twisted.internet import defer


class ReadOnlyLDAPServer(LDAPServer):
    def getRootDSE(  # noqa: N802
        self,
        request: LDAPBindRequest,
        reply: Callable[[LDAPSearchResultEntry], None] | None,
    ) -> LDAPSearchResultDone:
        """Handle an LDAP Root RSE request"""
        return super().getRootDSE(request, reply)

    def handle_LDAPAddRequest(  # noqa: N802
        self,
        request: LDAPBindRequest,
        controls: LDAPControl | None,
        reply: Callable[..., None] | None,
    ) -> defer.Deferred[ILDAPEntry]:
        """Refuse to handle an LDAP add request"""
        id((request, controls, reply))  # ignore unused arguments
        msg = "ReadOnlyLDAPServer will not handle LDAP add requests"
        raise LDAPProtocolError(msg)

    def handle_LDAPBindRequest(  # noqa: N802
        self,
        request: LDAPBindRequest,
        controls: LDAPControl | None,
        reply: Callable[..., None] | None,
    ) -> defer.Deferred[ILDAPEntry]:
        """Handle an LDAP bind request"""
        return super().handle_LDAPBindRequest(request, controls, reply)

    def handle_LDAPCompareRequest(  # noqa: N802
        self,
        request: LDAPBindRequest,
        controls: LDAPControl | None,
        reply: Callable[..., None] | None,
    ) -> defer.Deferred[ILDAPEntry]:
        """Handle an LDAP compare request"""
        return super().handle_LDAPCompareRequest(request, controls, reply)

    def handle_LDAPDelRequest(  # noqa: N802
        self,
        request: LDAPBindRequest,
        controls: LDAPControl | None,
        reply: Callable[..., None] | None,
    ) -> defer.Deferred[ILDAPEntry]:
        """Refuse to handle an LDAP delete request"""
        id((request, controls, reply))  # ignore unused arguments
        msg = "ReadOnlyLDAPServer will not handle LDAP delete requests"
        raise LDAPProtocolError(msg)

    def handle_LDAPExtendedRequest(  # noqa: N802
        self,
        request: LDAPBindRequest,
        controls: LDAPControl | None,
        reply: Callable[..., None] | None,
    ) -> defer.Deferred[ILDAPEntry]:
        """Handle an LDAP extended request"""
        return super().handle_LDAPExtendedRequest(request, controls, reply)

    def handle_LDAPModifyDNRequest(  # noqa: N802
        self,
        request: LDAPBindRequest,
        controls: LDAPControl | None,
        reply: Callable[..., None] | None,
    ) -> defer.Deferred[ILDAPEntry]:
        """Refuse to handle an LDAP modify DN request"""
        id((request, controls, reply))  # ignore unused arguments
        msg = "ReadOnlyLDAPServer will not handle LDAP modify DN requests"
        raise LDAPProtocolError(msg)

    def handle_LDAPModifyRequest(  # noqa: N802
        self,
        request: LDAPBindRequest,
        controls: LDAPControl | None,
        reply: Callable[..., None] | None,
    ) -> defer.Deferred[ILDAPEntry]:
        """Refuse to handle an LDAP modify request"""
        id((request, controls, reply))  # ignore unused arguments
        msg = "ReadOnlyLDAPServer will not handle LDAP modify requests"
        raise LDAPProtocolError(msg)

    def handle_LDAPUnbindRequest(  # noqa: N802
        self,
        request: LDAPBindRequest,
        controls: LDAPControl | None,
        reply: Callable[..., None] | None,
    ) -> None:
        """Handle an LDAP unbind request"""
        super().handle_LDAPUnbindRequest(request, controls, reply)

    def handle_LDAPSearchRequest(  # noqa: N802
        self,
        request: LDAPBindRequest,
        controls: LDAPControl | None,
        reply: Callable[[LDAPSearchResultEntry], None] | None,
    ) -> defer.Deferred[ILDAPEntry]:
        """Handle an LDAP search request"""
        return super().handle_LDAPSearchRequest(request, controls, reply)
