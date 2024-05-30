import argparse
import sys

from apricot import ApricotServer
from apricot.oauth import OAuthBackend

if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(
            prog="Apricot",
            description="Apricot is a proxy for delegating LDAP requests to an OpenID Connect backend.",
        )
        # Common options needed for all backends
        parser.add_argument(
            "-b",
            "--backend",
            type=OAuthBackend,
            help="Which OAuth backend to use.",
        )
        parser.add_argument(
            "-d",
            "--domain",
            type=str,
            help="Which domain users belong to.",
        )
        parser.add_argument("-i", "--client-id", type=str, help="OAuth client ID.")
        parser.add_argument(
            "-p",
            "--port",
            type=int,
            default=1389,
            help="Port to run on.",
        )
        parser.add_argument(
            "-s",
            "--client-secret",
            type=str,
            help="OAuth client secret.",
        )
        parser.add_argument(
            "--background-refresh",
            action="store_true",
            default=False,
            help="Refresh in the background instead of as needed per request",
        )
        parser.add_argument(
            "--debug",
            action="store_true",
            help="Enable debug logging.",
        )
        parser.add_argument(
            "--disable-mirrored-groups",
            action="store_false",
            default=True,
            dest="enable_mirrored_groups",
            help="Disable creation of mirrored groups.",
        )
        parser.add_argument(
            "--refresh-interval",
            type=int,
            default=60,
            help="How often to refresh the database in seconds",
        )

        # Options for Microsoft Entra backend
        entra_group = parser.add_argument_group("Microsoft Entra")
        entra_group.add_argument(
            "--entra-tenant-id",
            type=str,
            help="Microsoft Entra tenant ID.",
        )

        # Options for Keycloak backend
        keycloak_group = parser.add_argument_group("Keycloak")
        keycloak_group.add_argument(
            "--keycloak-base-url",
            type=str,
            help="Keycloak base URL.",
        )
        keycloak_group.add_argument(
            "--keycloak-realm",
            type=str,
            help="Keycloak Realm.",
        )
        # Options for Redis cache
        redis_group = parser.add_argument_group("Redis")
        redis_group.add_argument(
            "--redis-host",
            type=str,
            help="Host for Redis server.",
        )
        redis_group.add_argument(
            "--redis-port",
            type=int,
            help="Port for Redis server.",
        )
        # Options for TLS
        tls_group = parser.add_argument_group("TLS")
        tls_group.add_argument(
            "--tls-certificate",
            type=str,
            help="Location of TLS certificate (pem).",
        )
        tls_group.add_argument(
            "--tls-port",
            type=int,
            default=1636,
            help="Port to run on with encryption.",
        )
        tls_group.add_argument(
            "--tls-private-key",
            type=str,
            help="Location of TLS private key (pem).",
        )
        # Parse arguments
        args = parser.parse_args()

        # Create the Apricot server
        reactor = ApricotServer(**vars(args))
    except Exception as exc:  # noqa: BLE001
        msg = f"Unable to initialise Apricot server.\n{exc}"
        print(msg)  # noqa: T201
        sys.exit(1)

    # Run the Apricot server
    try:
        reactor.run()
    except Exception as exc:  # noqa: BLE001
        msg = f"Apricot server encountered a runtime problem.\n{exc}"
        print(msg)  # noqa: T201
        sys.exit(1)
