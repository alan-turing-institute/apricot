import argparse

from apricot import ApricotServer

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="Apricot",
        description="Apricot is a proxy for delegating LDAP requests to an OpenID Connect backend.",
    )
    parser.add_argument("-p", "--port", type=int, default=8080)
    args = parser.parse_args()

    # Create the Apricot server
    reactor = ApricotServer(port=args.port)
    reactor.run()
