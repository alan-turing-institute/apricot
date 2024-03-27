from typing import Callable

from ldaptor.interfaces import ILDAPEntry
from ldaptor.protocols.ldap.ldaperrors import LDAPProtocolError
from ldaptor.protocols.ldap.ldapserver import LDAPServer
from ldaptor.protocols.pureldap import (
    LDAPAddRequest,
    LDAPBindRequest,
    LDAPCompareRequest,
    LDAPDelRequest,
    LDAPExtendedRequest,
    LDAPModifyDNRequest,
    LDAPModifyRequest,
    LDAPProtocolRequest,
    LDAPSearchRequest,
    LDAPSearchResultDone,
    LDAPSearchResultEntry,
    LDAPUnbindRequest,
)
from twisted.internet import defer
from twisted.python import log

from apricot.oauth import LDAPControlTuple


class ReadOnlyLDAPServer(LDAPServer):
    def __init__(self, *, debug: bool = False) -> None:
        super().__init__()
        self.debug = debug

    def getRootDSE(  # noqa: N802
        self,
        request: LDAPProtocolRequest,
        reply: Callable[[LDAPSearchResultEntry], None] | None,
    ) -> LDAPSearchResultDone:
        """
        Handle an LDAP Root DSE request
        """
        if self.debug:
            log.msg("Handling an LDAP Root DSE request.")
        try:
            return super().getRootDSE(request, reply)
        except Exception as exc:
            msg = f"LDAP Root DSE request failed. {exc}"
            raise LDAPProtocolError(msg) from exc

    def handle_LDAPAddRequest(  # noqa: N802
        self,
        request: LDAPAddRequest,
        controls: list[LDAPControlTuple] | None,
        reply: Callable[..., None] | None,
    ) -> defer.Deferred[ILDAPEntry]:
        """
        Refuse to handle an LDAP add request
        """
        if self.debug:
            log.msg("Handling an LDAP add request.")
        id((request, controls, reply))  # ignore unused arguments
        msg = "ReadOnlyLDAPServer will not handle LDAP add requests"
        raise LDAPProtocolError(msg)

    def handle_LDAPBindRequest(  # noqa: N802
        self,
        request: LDAPBindRequest,
        controls: list[LDAPControlTuple] | None,
        reply: Callable[..., None] | None,
    ) -> defer.Deferred[ILDAPEntry]:
        """
        Handle an LDAP bind request
        """
        if self.debug:
            log.msg("Handling an LDAP bind request.")
        try:
            return super().handle_LDAPBindRequest(request, controls, reply)
        except Exception as exc:
            msg = f"LDAP bind request failed. {exc}"
            raise LDAPProtocolError(msg) from exc

    def handle_LDAPCompareRequest(  # noqa: N802
        self,
        request: LDAPCompareRequest,
        controls: list[LDAPControlTuple] | None,
        reply: Callable[..., None] | None,
    ) -> defer.Deferred[ILDAPEntry]:
        """
        Handle an LDAP compare request
        """
        if self.debug:
            log.msg("Handling an LDAP compare request.")
        try:
            return super().handle_LDAPCompareRequest(request, controls, reply)
        except Exception as exc:
            msg = f"LDAP compare request failed. {exc}"
            raise LDAPProtocolError(msg) from exc

    def handle_LDAPDelRequest(  # noqa: N802
        self,
        request: LDAPDelRequest,
        controls: list[LDAPControlTuple] | None,
        reply: Callable[..., None] | None,
    ) -> defer.Deferred[ILDAPEntry]:
        """
        Refuse to handle an LDAP delete request
        """
        if self.debug:
            log.msg("Handling an LDAP delete request.")
        id((request, controls, reply))  # ignore unused arguments
        msg = "ReadOnlyLDAPServer will not handle LDAP delete requests"
        raise LDAPProtocolError(msg)

    def handle_LDAPExtendedRequest(  # noqa: N802
        self,
        request: LDAPExtendedRequest,
        controls: list[LDAPControlTuple] | None,
        reply: Callable[..., None] | None,
    ) -> defer.Deferred[ILDAPEntry]:
        """
        Handle an LDAP extended request
        """
        if self.debug:
            log.msg("Handling an LDAP extended request.")
        try:
            return super().handle_LDAPExtendedRequest(request, controls, reply)
        except Exception as exc:
            msg = f"LDAP extended request failed. {exc}"
            raise LDAPProtocolError(msg) from exc

    def handle_LDAPModifyDNRequest(  # noqa: N802
        self,
        request: LDAPModifyDNRequest,
        controls: list[LDAPControlTuple] | None,
        reply: Callable[..., None] | None,
    ) -> defer.Deferred[ILDAPEntry]:
        """
        Refuse to handle an LDAP modify DN request
        """
        if self.debug:
            log.msg("Handling an LDAP modify DN request.")
        id((request, controls, reply))  # ignore unused arguments
        msg = "ReadOnlyLDAPServer will not handle LDAP modify DN requests"
        raise LDAPProtocolError(msg)

    def handle_LDAPModifyRequest(  # noqa: N802
        self,
        request: LDAPModifyRequest,
        controls: list[LDAPControlTuple] | None,
        reply: Callable[..., None] | None,
    ) -> defer.Deferred[ILDAPEntry]:
        """
        Refuse to handle an LDAP modify request
        """
        if self.debug:
            log.msg("Handling an LDAP modify request.")
        id((request, controls, reply))  # ignore unused arguments
        msg = "ReadOnlyLDAPServer will not handle LDAP modify requests"
        raise LDAPProtocolError(msg)

    def handle_LDAPSearchRequest(  # noqa: N802
        self,
        request: LDAPSearchRequest,
        controls: list[LDAPControlTuple] | None,
        reply: Callable[[LDAPSearchResultEntry], None] | None,
    ) -> defer.Deferred[ILDAPEntry]:
        """
        Handle an LDAP search request
        """
        if self.debug:
            log.msg("Handling an LDAP search request.")
        try:
            return super().handle_LDAPSearchRequest(request, controls, reply)
        except Exception as exc:
            msg = f"LDAP search request failed. {exc}"
            raise LDAPProtocolError(msg) from exc

    def handle_LDAPUnbindRequest(  # noqa: N802
        self,
        request: LDAPUnbindRequest,
        controls: list[LDAPControlTuple] | None,
        reply: Callable[..., None] | None,
    ) -> None:
        """
        Handle an LDAP unbind request
        """
        if self.debug:
            log.msg("Handling an LDAP unbind request.")
        try:
            super().handle_LDAPUnbindRequest(request, controls, reply)
        except Exception as exc:
            msg = f"LDAP unbind request failed. {exc}"
            raise LDAPProtocolError(msg) from exc
