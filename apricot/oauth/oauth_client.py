import os
from abc import ABC, abstractmethod
from typing import Any

from oauthlib.oauth2 import (
    BackendApplicationClient,
    InvalidGrantError,
    LegacyApplicationClient,
)
from requests_oauthlib import OAuth2Session
from twisted.python import log

from .types import JSONDict, LDAPAttributeDict


class OAuthClient(ABC):
    """Base class for OAuth client talking to a generic backend."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        domain: str,
        redirect_uri: str,
        scopes: list[str],
        token_url: str,
    ) -> None:
        # Set attributes
        self.client_secret = client_secret
        self.domain = domain
        self.token_url = token_url
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
        # Request a new bearer token
        json_response = self.session_application.fetch_token(
            token_url=self.token_url,
            client_id=self.session_application._client.client_id,
            client_secret=self.client_secret,
        )
        self.bearer_token = self.extract_token(json_response)

    @abstractmethod
    def extract_token(self, json_response: JSONDict) -> str:
        pass

    @abstractmethod
    def groups(self) -> list[LDAPAttributeDict]:
        pass

    @abstractmethod
    def users(self) -> list[LDAPAttributeDict]:
        pass

    @property
    def root_dn(self) -> str:
        return "DC=" + self.domain.replace(".", ",DC=")

    def query(self, url: str) -> dict[str, Any]:
        result = self.session_application.request(
            method="GET",
            url=url,
            headers={"Authorization": f"Bearer {self.bearer_token}"},
            client_id=self.session_application._client.client_id,
            client_secret=self.client_secret,
        )
        return result.json()  # type: ignore

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
