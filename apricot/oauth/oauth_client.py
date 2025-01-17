from __future__ import annotations

import os
from abc import ABC, abstractmethod
from http import HTTPStatus
from typing import TYPE_CHECKING, Any, Self

import requests
from oauthlib.oauth2 import (
    BackendApplicationClient,
    InvalidClientIdError,
    InvalidGrantError,
    LegacyApplicationClient,
    TokenExpiredError,
)
from requests_oauthlib import OAuth2Session
from twisted.logger import Logger

if TYPE_CHECKING:
    from apricot.cache import UidCache
    from apricot.typedefs import JSONDict


class OAuthClient(ABC):
    """Base class for OAuth client talking to a generic backend."""

    def __init__(  # noqa: PLR0913
        self: Self,
        *,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        scopes_application: list[str],
        scopes_delegated: list[str],
        token_url: str,
        uid_cache: UidCache,
    ) -> None:
        """Initialise an OAuthClient.

        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret
            redirect_uri: OAuth redirect URI
            scopes_application: OAuth scopes for a client using application credentials
            scopes_delegated: OAuth scopes for a client using delegated credentials
            token_url: OAuth token URL
            uid_cache: Cache for UIDs

        Raises:
            RuntimeError: if the OAuth client could not be initialised
        """
        # Set attributes
        self.bearer_token_: str | None = None
        self.client_secret = client_secret
        self.logger = Logger()
        self.token_url = token_url
        self.uid_cache = uid_cache
        # Allow token scope to not match requested scope. (Other auth libraries allow
        # this, but Requests-OAuthlib raises exception on scope mismatch by default.)
        os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"  # noqa: S105
        os.environ["OAUTHLIB_IGNORE_SCOPE_CHANGE"] = "1"

        try:
            # OAuth client that uses application credentials
            self.logger.debug("Initialising application credential client.")
            self.session_application = OAuth2Session(
                client=BackendApplicationClient(
                    client_id=client_id,
                    scope=scopes_application,
                    redirect_uri=redirect_uri,
                ),
            )
        except Exception as exc:
            msg = f"Failed to initialise application credential client.\n{exc!s}"
            raise RuntimeError(msg) from exc

        try:
            # OAuth client that uses delegated credentials
            self.logger.debug("Initialising delegated credential client.")
            self.session_interactive = OAuth2Session(
                client=LegacyApplicationClient(
                    client_id=client_id,
                    scope=scopes_delegated,
                    redirect_uri=redirect_uri,
                ),
            )
        except Exception as exc:
            msg = f"Failed to initialise delegated credential client.\n{exc!s}"
            self.logger.error(msg)  # noqa: TRY400
            raise RuntimeError(msg) from exc

    @property
    def bearer_token(self: Self) -> str:
        """Return a bearer token, requesting a new one if necessary.

        Returns:
            An OAuth bearer token

        Raises:
            RuntimeError: if a bearer token could not be retrieved
        """
        try:
            if not self.bearer_token_:
                self.logger.info(
                    "Requesting a new authentication token from the OAuth backend.",
                )
                json_response = self.session_application.fetch_token(
                    token_url=self.token_url,
                    client_secret=self.client_secret,
                )
                self.bearer_token_ = self.extract_token(json_response)
        except Exception as exc:
            msg = f"Failed to fetch bearer token from OAuth endpoint.\n{exc!s}"
            self.logger.error(msg)  # noqa: TRY400
            raise RuntimeError(msg) from exc
        else:
            return self.bearer_token_

    @staticmethod
    @abstractmethod
    def extract_token(json_response: JSONDict) -> str:
        """Extract the bearer token from an OAuth2Session JSON response."""

    @abstractmethod
    def groups(self: Self) -> list[JSONDict]:
        """Return JSON data about groups from the OAuth backend.

        This should be a list of JSON dictionaries where 'None' is used to signify
        missing values.

        Returns:
            A list of group data in JSON format
        """

    @abstractmethod
    def users(self: Self) -> list[JSONDict]:
        """Return JSON data about users from the OAuth backend.

        This should be a list of JSON dictionaries where 'None' is used to signify
        missing values.

        Returns:
            A list of user data in JSON format
        """

    def query(
        self: Self,
        url: str,
        *,
        use_client_secret: bool = True,
    ) -> dict[str, Any]:
        """Make a query against the OAuth backend.

        Args:
            url: Which backend URL to send the query to.
            use_client_secret: Whether to send the client secret with the query

        Returns:
            The JSON response from the OAuth backend.
        """
        kwargs = {"client_secret": self.client_secret} if use_client_secret else {}
        return self.request(
            url=url,
            method="GET",
            **kwargs,
        )

    def request(
        self: Self,
        *args: Any,
        method: str = "GET",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make a request to the OAuth backend.

        Args:
            method: Which HTTP request method to use
            args: Arguments to send with the request
            kwargs: Keyword arguments to send with the request

        Returns:
            The JSON response from the OAuth backend.
        """

        def request_(*args: Any, **kwargs: Any) -> requests.Response:
            return self.session_application.request(  # type: ignore[no-any-return]
                method,
                *args,
                **kwargs,
                headers={"Authorization": f"Bearer {self.bearer_token}"},
            )

        try:
            result = request_(*args, **kwargs)
            result.raise_for_status()
        except (TokenExpiredError, requests.exceptions.HTTPError) as exc:
            self.logger.warn("Authentication token is invalid. {error}", error=exc)
            self.bearer_token_ = None
            result = request_(*args, **kwargs)
        if result.status_code == HTTPStatus.NO_CONTENT:
            return {}
        return result.json()  # type: ignore[no-any-return]

    def verify(self: Self, username: str, password: str) -> bool:
        """Verify username and password.

        This is done by attempting to authenticate against the OAuth backend.

        Args:
            username: Username
            password: User password

        Returns:
            Whether the username and password were correct
        """
        try:
            self.session_interactive.fetch_token(
                token_url=self.token_url,
                username=username,
                password=password,
                client_secret=self.client_secret,
            )
        except (InvalidClientIdError, InvalidGrantError) as exc:
            self.logger.warn(
                "Authentication failed for user '{user}'. {error}",
                user=username,
                error=str(exc),
            )
            return False
        else:
            return True
