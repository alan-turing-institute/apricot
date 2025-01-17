from __future__ import annotations

import inspect
import logging
from typing import TYPE_CHECKING, Any, Self, cast

from twisted.internet import reactor, task
from twisted.internet.endpoints import quoteStringArgument, serverFromString
from twisted.logger import Logger
from twisted.python import log

from apricot.cache import LocalCache, RedisCache, UidCache
from apricot.ldap import OAuthLDAPServerFactory
from apricot.oauth import OAuthBackend, OAuthClientMap, OAuthDataAdaptor

if TYPE_CHECKING:
    from twisted.internet.interfaces import IReactorCore, IStreamServerEndpoint


class ApricotServer:
    """The Apricot server running via Twisted."""

    def __init__(  # noqa: PLR0913
        self: Self,
        backend: OAuthBackend,
        client_id: str,
        client_secret: str,
        domain: str,
        port: int,
        *,
        allow_anonymous_binds: bool = True,
        background_refresh: bool = False,
        debug: bool = False,
        enable_mirrored_groups: bool = True,
        enable_primary_groups: bool = True,
        enable_user_domain_verification: bool = True,
        redis_host: str | None = None,
        redis_port: int | None = None,
        refresh_interval: int = 60,
        tls_port: int | None = None,
        tls_certificate: str | None = None,
        tls_private_key: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialise an ApricotServer.

        Args:
            allow_anonymous_binds: Whether to allow anonymous LDAP binds
            backend: An OAuth backend,
            client_id: An OAuth client ID
            client_secret: An OAuth client secret
            domain: The OAuth domain
            port: Port to expose LDAP on
            background_refresh: Whether to refresh the LDAP tree in the background
            debug: Enable debug output
            enable_mirrored_groups: Whether to create a mirrored LDAP group-of-groups
                for each group-of-users
            enable_primary_groups: Whether to create an LDAP primary group for each user
            enable_user_domain_verification: Whether to verify users belong to the
                correct domain
            redis_host: Host for a Redis cache (if used)
            redis_port: Port for a Redis cache (if used)
            refresh_interval: Interval after which the LDAP information is stale
            tls_port: Port to expose LDAPS on
            tls_certificate: TLS certificate for LDAPS
            tls_private_key: TLS private key for LDAPS
            kwargs: Backend-dependent arguments

        Raises:
            ValueError: if the OAuth backend could not be initialised
        """
        # Set up Python root logger
        logging.basicConfig(
            level=logging.INFO,
            datefmt=r"%Y-%m-%d %H:%M:%S",
            format=r"%(asctime)s [%(levelname)-8s] %(message)s",
        )
        if debug:
            logging.getLogger("apricot").setLevel(logging.DEBUG)

        # Configure Twisted loggers to write to Python logging
        observer = log.PythonLoggingObserver("apricot")
        observer.start()
        self.logger = Logger()

        # Load the Twisted reactor
        self.reactor = cast("IReactorCore", reactor)

        # Initialise the UID cache
        uid_cache: UidCache
        if redis_host and redis_port:
            self.logger.info(
                "Using a Redis user-id cache at port {port} on host {host}.",
                host=redis_host,
                port=redis_port,
            )
            uid_cache = RedisCache(redis_host=redis_host, redis_port=redis_port)
        else:
            self.logger.info("Using a local user-id cache.")
            uid_cache = LocalCache()

        # Initialise the appropriate OAuth client
        try:
            self.logger.debug(
                "Creating an OAuthClient for the {backend} backend.",
                backend=backend.value,
            )
            oauth_backend = OAuthClientMap[backend]
            oauth_backend_args = inspect.getfullargspec(
                oauth_backend.__init__,  # type: ignore[misc]
            ).args
            oauth_client = oauth_backend(
                client_id=client_id,
                client_secret=client_secret,
                uid_cache=uid_cache,
                **{k: v for k, v in kwargs.items() if k in oauth_backend_args},
            )
        except Exception as exc:
            msg = (
                f"Could not construct an OAuth client for the {backend.value} backend."
                f"\n{exc!s}"
            )
            raise ValueError(msg) from exc

        # Initialise the OAuth data adaptor
        self.logger.debug("Creating an OAuthDataAdaptor.")
        oauth_adaptor = OAuthDataAdaptor(
            domain,
            oauth_client,
            enable_mirrored_groups=enable_mirrored_groups,
            enable_primary_groups=enable_primary_groups,
            enable_user_domain_verification=enable_user_domain_verification,
        )

        # Create an OAuthLDAPServerFactory
        self.logger.debug("Creating an OAuthLDAPServerFactory.")
        factory = OAuthLDAPServerFactory(
            oauth_adaptor,
            oauth_client,
            allow_anonymous_binds=allow_anonymous_binds,
            background_refresh=background_refresh,
            refresh_interval=refresh_interval,
        )

        if background_refresh:
            self.logger.info(
                "Starting background refresh (interval={interval})",
                interval=refresh_interval,
            )
            loop = task.LoopingCall(factory.adaptor.refresh)
            loop.start(refresh_interval)

        # Attach a listening endpoint
        self.logger.info("Listening for LDAP requests on port {port}.", port=port)
        endpoint: IStreamServerEndpoint = serverFromString(self.reactor, f"tcp:{port}")
        endpoint.listen(factory)

        # Attach a listening endpoint
        if tls_certificate or tls_private_key:
            if not tls_certificate:
                msg = (
                    "No TLS certificate provided."
                    "Please provide one with --tls-certificate or disable TLS."
                )
                raise ValueError(msg)
            if not tls_private_key:
                msg = (
                    "No TLS private key provided."
                    "Please provide one with --tls-private-key or disable TLS."
                )
                raise ValueError(msg)
            self.logger.info(
                "Listening for LDAPS requests on port {port}.",
                port=tls_port,
            )
            ssl_endpoint: IStreamServerEndpoint = serverFromString(
                self.reactor,
                ":".join(
                    (
                        f"ssl:{tls_port}",
                        f"privateKey={quoteStringArgument(tls_private_key)}",
                        f"certKey={quoteStringArgument(tls_certificate)}",
                    ),
                ),
            )
            ssl_endpoint.listen(factory)

    def run(self: Self) -> None:
        """Start the Twisted reactor."""
        self.reactor.run()
