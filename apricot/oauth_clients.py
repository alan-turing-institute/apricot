import os
from enum import Enum
from typing import Any

from oauthlib.oauth2 import (
    BackendApplicationClient,
    InvalidGrantError,
    LegacyApplicationClient,
)
from requests_oauthlib import OAuth2Session
from twisted.python import log

LDAPEntryList = list[dict[str, list[Any]]]


class OAuthBackend(str, Enum):
    """Available OAuth backends."""

    MICROSOFT_ENTRA = "MicrosoftEntra"


class OAuthClient:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        scopes: list[str],
        token_url: str,
    ) -> None:
        # Allow token scope to not match requested scope. (Other auth libraries allow
        # this, but Requests-OAuthlib raises exception on scope mismatch by default.)
        os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"  # noqa: S105
        os.environ["OAUTHLIB_IGNORE_SCOPE_CHANGE"] = "1"
        # OAuth client that uses application credentials
        self.session_application = OAuth2Session(
            client=BackendApplicationClient(
                client_id=client_id, scope=scopes, redirect_uri=redirect_uri
            )
        )
        # OAuth client that uses delegated credentials
        self.session_interactive = OAuth2Session(
            client=LegacyApplicationClient(
                client_id=client_id, scope=scopes, redirect_uri=redirect_uri
            )
        )
        # Store client secret and token URL
        self.client_secret = client_secret
        self.token_url = token_url
        # Request a new bearer token
        json_response = self.session_application.fetch_token(
            token_url=self.token_url,
            client_id=self.session_application._client.client_id,
            client_secret=self.client_secret,
        )
        self.bearer_token = self.extract_token(json_response)

    def extract_token(self, json_response: dict[str, str | list[str]]) -> str:
        id(json_response)
        raise NotImplementedError

    def query(self, url: str) -> dict[str, Any]:
        result = self.session_application.request(
            method="GET",
            url=url,
            headers={"Authorization": f"Bearer {self.bearer_token}"},
            client_id=self.session_application._client.client_id,
            client_secret=self.client_secret,
        )
        return result.json()

    def domain(self) -> str:
        raise NotImplementedError

    def groups(self) -> LDAPEntryList:
        raise NotImplementedError

    def users(self) -> LDAPEntryList:
        raise NotImplementedError

    def verify(self, username: str, password: str) -> bool:
        try:
            self.session_interactive.fetch_token(
                token_url=self.token_url,
                username=username,
                password=password,
                client_id=self.session_interactive._client.client_id,
                client_secret=self.client_secret,
            )
            return True
        except InvalidGrantError as exc:
            log.msg(f"Authentication failed.\n{exc}")
        return False


class MicrosoftEntraClient(OAuthClient):
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        tenant_id: str,
        *args: Any,
        **kwargs: Any,
    ):
        redirect_uri = "urn:ietf:wg:oauth:2.0:oob"  # this is the "no redirect" URL
        scopes = ["https://graph.microsoft.com/.default"]  # this is the default scope
        token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
        self.tenant_id = tenant_id
        super().__init__(
            *args,
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scopes=scopes,
            token_url=token_url,
            **kwargs,
        )

    def domain(self) -> str:
        users = self.users()
        domains = {user["domain"][0] for user in users}
        if len(domains) > 1:
            domains = [domain for domain in domains if "onmicrosoft.com" not in domain]
        return sorted(domains)[0]

    def extract_token(self, json_response: dict[str, str | list[str]]) -> None:
        return json_response["access_token"]

    def groups(self) -> LDAPEntryList:
        output = []
        try:
            group_data = self.query("https://graph.microsoft.com/v1.0/groups/")
            for group_dict in group_data["value"]:
                attributes = {k: [v if v else ""] for k, v in dict(group_dict).items()}
                attributes["objectclass"] = ["top", "group"]
                attributes["name"] = [str(group_dict["displayName"]).split("@")[0]]
                output.append(attributes)
        except KeyError:
            pass
        return output

    def users(self) -> LDAPEntryList:
        output = []
        try:
            user_data = self.query("https://graph.microsoft.com/v1.0/users/")
            for user_dict in user_data["value"]:
                attributes = {k: [v if v else ""] for k, v in dict(user_dict).items()}
                attributes["objectclass"] = [
                    "top",
                    "person",
                    "organizationalPerson",
                    "user",
                ]
                group_memberships = self.query(
                    f"https://graph.microsoft.com/v1.0/users/{user_dict['id']}/memberOf"
                )
                attributes["memberOf"] = [
                    group["displayName"]
                    for group in group_memberships["value"]
                    if group["displayName"]
                ]
                attributes["name"] = [str(user_dict["userPrincipalName"]).split("@")[0]]
                attributes["domain"] = [
                    str(user_dict["userPrincipalName"]).split("@")[1]
                ]
                output.append(attributes)
        except KeyError:
            pass
        return output
