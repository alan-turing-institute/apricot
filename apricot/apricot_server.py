from __future__ import annotations

import inspect
import sys
from typing import Any, Self, cast

from twisted.internet import reactor, task
from twisted.internet.endpoints import quoteStringArgument, serverFromString
from twisted.internet.interfaces import IReactorCore, IStreamServerEndpoint
from twisted.python import log

from apricot.cache import LocalCache, RedisCache, UidCache
from apricot.ldap import OAuthLDAPServerFactory
from apricot.oauth import OAuthBackend, OAuthClientMap


class ApricotServer:
    """The Apricot server running via Twisted."""

    def __init__(
        self: Self,
        backend: OAuthBackend,
        client_id: str,
        client_secret: str,
        domain: str,
        port: int,
        *,
        background_refresh: bool = False,
        debug: bool = False,
        enable_mirrored_groups: bool = True,
        redis_host: str | None = None,
        redis_port: int | None = None,
        refresh_interval: int = 60,
        tls_port: int | None = None,
        tls_certificate: str | None = None,
        tls_private_key: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialise an ApricotServer.

        @param backend: An OAuth backend,
        @param client_id: An OAuth client ID
        @param client_secret: An OAuth client secret
        @param domain: The OAuth domain
        @param port: Port to expose LDAP on
        @param background_refresh: Whether to refresh the LDAP tree in the background
        @param debug: Enable debug output
        @param enable_mirrored_groups: Create a mirrored LDAP group-of-groups for each group-of-users
        @param redis_host: Host for a Redis cache (if used)
        @param redis_port: Port for a Redis cache (if used)
        @param refresh_interval: Interval after which the LDAP information is stale
        @param tls_port: Port to expose LDAPS on
        @param tls_certificate: TLS certificate for LDAPS
        @param tls_private_key: TLS private key for LDAPS
        """
        self.debug = debug

        # Log to stdout
        log.startLogging(sys.stdout)

        # Initialise the UID cache
        uid_cache: UidCache
        if redis_host and redis_port:
            log.msg(
                f"Using a Redis user-id cache at host '{redis_host}' on port '{redis_port}'.",
            )
            uid_cache = RedisCache(redis_host=redis_host, redis_port=redis_port)
        else:
            log.msg("Using a local user-id cache.")
            uid_cache = LocalCache()

        # Initialize the appropriate OAuth client
        try:
            if self.debug:
                log.msg(f"Creating an OAuthClient for {backend}.")
            oauth_backend = OAuthClientMap[backend]
            oauth_backend_args = inspect.getfullargspec(
                oauth_backend.__init__,  # type: ignore[misc]
            ).args
            oauth_client = oauth_backend(
                client_id=client_id,
                client_secret=client_secret,
                debug=debug,
                uid_cache=uid_cache,
                **{k: v for k, v in kwargs.items() if k in oauth_backend_args},
            )
        except Exception as exc:
            msg = f"Could not construct an OAuth client for the '{backend}' backend.\n{exc!s}"
            raise ValueError(msg) from exc

        # Create an LDAPServerFactory
        if self.debug:
            log.msg("Creating an LDAPServerFactory.")
        factory = OAuthLDAPServerFactory(
            domain,
            oauth_client,
            background_refresh=background_refresh,
            enable_mirrored_groups=enable_mirrored_groups,
            refresh_interval=refresh_interval,
        )

        if background_refresh:
            if self.debug:
                log.msg(
                    f"Starting background refresh (interval={factory.adaptor.refresh_interval})",
                )
            loop = task.LoopingCall(factory.adaptor.refresh)
            loop.start(factory.adaptor.refresh_interval)

        # Attach a listening endpoint
        if self.debug:
            log.msg("Attaching a listening endpoint (plain).")
        endpoint: IStreamServerEndpoint = serverFromString(reactor, f"tcp:{port}")
        endpoint.listen(factory)

        # Attach a listening endpoint
        if tls_certificate or tls_private_key:
            if not tls_certificate:
                msg = "No TLS certificate provided. Please provide one with --tls-certificate or disable TLS."
                raise ValueError(msg)
            if not tls_private_key:
                msg = "No TLS private key provided. Please provide one with --tls-private-key or disable TLS."
                raise ValueError(msg)
            if self.debug:
                log.msg("Attaching a listening endpoint (TLS).")
            ssl_endpoint: IStreamServerEndpoint = serverFromString(
                reactor,
                f"ssl:{tls_port}:privateKey={quoteStringArgument(tls_private_key)}:certKey={quoteStringArgument(tls_certificate)}",
            )
            ssl_endpoint.listen(factory)

        # Load the Twisted reactor
        self.reactor = cast(IReactorCore, reactor)

    def run(self: Self) -> None:
        """Start the Twisted reactor."""
        if self.debug:
            log.msg("Starting the Twisted reactor.")
        self.reactor.run()
