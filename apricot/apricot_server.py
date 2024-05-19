import inspect
import sys
from typing import Any, cast, Optional

from twisted.internet import reactor, task
from twisted.internet.endpoints import serverFromString, quoteStringArgument
from twisted.internet.interfaces import IReactorCore, IStreamServerEndpoint
from twisted.python import log

from apricot.cache import LocalCache, RedisCache, UidCache
from apricot.ldap import OAuthLDAPServerFactory
from apricot.oauth import OAuthBackend, OAuthClientMap


class ApricotServer:
    def __init__(
        self,
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
        tls_port: Optional[int] = None,
        tls_certificate: Optional[str] = None,
        tls_private_key: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        self.debug = debug

        # Log to stdout
        log.startLogging(sys.stdout)

        # Initialise the UID cache
        uid_cache: UidCache
        if redis_host and redis_port:
            log.msg(
                f"Using a Redis user-id cache at host '{redis_host}' on port '{redis_port}'."
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
                oauth_backend.__init__  # type: ignore
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
            domain, oauth_client, background_refresh=background_refresh, enable_mirrored_groups=enable_mirrored_groups, refresh_interval=refresh_interval
        )

        if background_refresh:
            if self.debug:
                log.msg(f"Starting background refresh (interval={factory.adaptor.refresh_interval})")
            loop = task.LoopingCall(factory.adaptor.refresh)
            loop.start(factory.adaptor.refresh_interval)

        # Attach a listening endpoint
        if self.debug:
            log.msg("Attaching a listening endpoint (plain).")
        endpoint: IStreamServerEndpoint = serverFromString(reactor, f"tcp:{port}")
        endpoint.listen(factory)

        # Attach a listening endpoint
        if tls_port:
            if not (tls_certificate or tls_private_key):
                raise ValueError("No TLS certificate or private key provided. Make sure you provide these parameters or disable TLS by not providing the TLS port")
            if self.debug:
                log.msg("Attaching a listening endpoint (TLS).")
            ssl_endpoint: IStreamServerEndpoint = serverFromString(reactor, f"ssl:{tls_port}:privateKey={quoteStringArgument(tls_private_key)}:certKey={quoteStringArgument(tls_certificate)}")
            ssl_endpoint.listen(factory)

        # Load the Twisted reactor
        self.reactor = cast(IReactorCore, reactor)

    def run(self) -> None:
        """Start the Twisted reactor"""
        if self.debug:
            log.msg("Starting the Twisted reactor.")
        self.reactor.run()
