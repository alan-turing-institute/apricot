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
        parser.add_argument("-b", "--backend", type=OAuthBackend, help="Which OAuth backend to use.")
        parser.add_argument("-d", "--domain", type=str, help="Which domain users belong to.")
        parser.add_argument("-i", "--client-id", type=str, help="OAuth client ID.")
        parser.add_argument("-p", "--port", type=int, default=1389, help="Port to run on.")
        parser.add_argument("-s", "--client-secret", type=str, help="OAuth client secret.")
        parser.add_argument("--disable-group-of-groups", action="store_false",
                             dest="enable_group_of_groups", default=True,
                             help="Disable creation of group-of-groups.")
        parser.add_argument("--debug", action="store_true", help="Enable debug logging.")
        # Options for Microsoft Entra backend
        entra_group = parser.add_argument_group("Microsoft Entra")
        entra_group.add_argument("-t", "--entra-tenant-id", type=str, help="Microsoft Entra tenant ID.", required=False)

        # Options for Keycloak backend
        keycloak_group = parser.add_argument_group("Keycloak")
        keycloak_group.add_argument("--keycloak-base-url", type=str, help="Keycloak base URL.", required=False)
        keycloak_group.add_argument("--keycloak-realm", type=str, help="Keycloak Realm.", required=False)
        # Options for Redis cache
        redis_group = parser.add_argument_group("Redis")
        redis_group.add_argument("--redis-host", type=str, help="Host for Redis server.")
        redis_group.add_argument("--redis-port", type=int, help="Port for Redis server.")
        # Parse arguments
        args = parser.parse_args()

        # Create the Apricot server
        reactor = ApricotServer(**vars(args))
    except Exception as exc:
        msg = f"Unable to initialise Apricot server.\n{exc}"
        print(msg)
        sys.exit(1)

    # Run the Apricot server
    try:
        reactor.run()
    except Exception as exc:
        msg = f"Apricot server encountered a runtime problem.\n{exc}"
        print(msg)
        sys.exit(1)
