import sys
from typing import Any, cast

from twisted.internet import reactor
from twisted.internet.endpoints import serverFromString
from twisted.internet.interfaces import IReactorCore, IStreamServerEndpoint
from twisted.python import log

from apricot.cache import LocalCache, RedisCache
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
        redis_host: str | None = None,
        redis_port: int | None = None,
        **kwargs: Any,
    ) -> None:
        # Log to stdout
        log.startLogging(sys.stdout)

        # Initialise the UID cache
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
            oauth_client = OAuthClientMap[backend](
                client_id=client_id,
                client_secret=client_secret,
                domain=domain,
                uid_cache=uid_cache,
                **kwargs,
            )
        except Exception as exc:
            msg = f"Could not construct an OAuth client for the '{backend}' backend.\n{exc!s}"
            raise ValueError(msg) from exc

        # Create an LDAPServerFactory
        factory = OAuthLDAPServerFactory(oauth_client)

        # Attach a listening endpoint
        endpoint: IStreamServerEndpoint = serverFromString(reactor, f"tcp:{port}")
        endpoint.listen(factory)

        # Load the Twisted reactor
        self.reactor = cast(IReactorCore, reactor)

    def run(self) -> None:
        """Start the Twisted reactor"""
        self.reactor.run()
