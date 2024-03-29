import os
from abc import ABC, abstractmethod
from typing import Any

import requests
from oauthlib.oauth2 import (
    BackendApplicationClient,
    InvalidGrantError,
    LegacyApplicationClient,
    TokenExpiredError,
)
from pydantic import ValidationError
from requests_oauthlib import OAuth2Session
from twisted.python import log

from apricot.cache import UidCache
from apricot.models import (
    LDAPAttributeAdaptor,
    LDAPGroupOfNames,
    LDAPInetOrgPerson,
    LDAPInetUser,
    LDAPOAuthUser,
    LDAPPerson,
    LDAPPosixAccount,
    LDAPPosixGroup,
)
from apricot.types import JSONDict


class OAuthClient(ABC):
    """Base class for OAuth client talking to a generic backend."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        debug: bool,  # noqa: FBT001
        domain: str,
        redirect_uri: str,
        scopes: list[str],
        token_url: str,
        uid_cache: UidCache,
    ) -> None:
        # Set attributes
        self.bearer_token_: str | None = None
        self.client_secret = client_secret
        self.debug = debug
        self.domain = domain
        self.token_url = token_url
        self.uid_cache = uid_cache
        # Allow token scope to not match requested scope. (Other auth libraries allow
        # this, but Requests-OAuthlib raises exception on scope mismatch by default.)
        os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"  # noqa: S105
        os.environ["OAUTHLIB_IGNORE_SCOPE_CHANGE"] = "1"

        try:
            # OAuth client that uses application credentials
            if self.debug:
                log.msg("Initialising application credential client.")
            self.session_application = OAuth2Session(
                client=BackendApplicationClient(
                    client_id=client_id, scope=scopes, redirect_uri=redirect_uri
                )
            )
        except Exception as exc:
            msg = f"Failed to initialise application credential client.\n{exc!s}"
            raise RuntimeError(msg) from exc

        try:
            # OAuth client that uses delegated credentials
            if self.debug:
                log.msg("Initialising delegated credential client.")
            self.session_interactive = OAuth2Session(
                client=LegacyApplicationClient(
                    client_id=client_id, scope=scopes, redirect_uri=redirect_uri
                )
            )
        except Exception as exc:
            msg = f"Failed to initialise delegated credential client.\n{exc!s}"
            raise RuntimeError(msg) from exc

    @property
    def bearer_token(self) -> str:
        """Return a bearer token, requesting a new one if necessary"""
        try:
            if not self.bearer_token_:
                log.msg("Requesting a new authentication token from the OAuth backend.")
                json_response = self.session_application.fetch_token(
                    token_url=self.token_url,
                    client_id=self.session_application._client.client_id,
                    client_secret=self.client_secret,
                )
                self.bearer_token_ = self.extract_token(json_response)
            return self.bearer_token_
        except Exception as exc:
            msg = f"Failed to fetch bearer token from OAuth endpoint.\n{exc!s}"
            raise RuntimeError(msg) from exc

    @abstractmethod
    def extract_token(self, json_response: JSONDict) -> str:
        """
        Extract the bearer token from an OAuth2Session JSON response
        """
        pass

    @abstractmethod
    def groups(self) -> list[dict[str, Any]]:
        """
        Return a list of group data

        Each return value should be a dict where 'None' is used to signify a missing value
        """
        pass

    @abstractmethod
    def users(self) -> list[dict[str, Any]]:
        """
        Return a list of user data

        Each return value should be a dict where 'None' is used to signify a missing value
        """
        pass

    @property
    def root_dn(self) -> str:
        return "DC=" + self.domain.replace(".", ",DC=")

    def query(self, url: str) -> dict[str, Any]:
        """
        Make a query against the OAuth backend
        """

        def query_(url: str) -> requests.Response:
            return self.session_application.get(  # type: ignore[no-any-return]
                url=url,
                headers={"Authorization": f"Bearer {self.bearer_token}"},
                client_id=self.session_application._client.client_id,
                client_secret=self.client_secret,
            )

        try:
            result = query_(url)
            result.raise_for_status()
        except (TokenExpiredError, requests.exceptions.HTTPError):
            log.msg("Authentication token has expired.")
            self.bearer_token_ = None
            result = query_(url)
        return result.json()  # type: ignore

    def validated_groups(self) -> list[LDAPAttributeAdaptor]:
        """
        Validate output via pydantic and return a list of LDAPAttributeAdaptor
        """
        if self.debug:
            log.msg("Constructing and validating list of groups")
        output = []
        # Add one self-titled group for each user
        user_group_dicts = []
        for user_dict in self.users():
            user_dict["memberUid"] = [user_dict["uid"]]
            user_dict["member"] = [f"CN={user_dict['cn']},OU=users,{self.root_dn}"]
            # Group name is taken from 'cn' which should match the username
            user_dict["cn"] = user_dict["uid"]
            user_group_dicts.append(user_dict)
        # Iterate over groups and validate them
        for group_dict in self.groups() + user_group_dicts:
            try:
                attributes = {"objectclass": ["top"]}
                # Add 'groupOfNames' attributes
                group_of_names = LDAPGroupOfNames(**group_dict)
                attributes.update(group_of_names.model_dump())
                attributes["objectclass"].append("groupOfNames")
                # Add 'posixGroup' attributes
                posix_group = LDAPPosixGroup(**group_dict)
                attributes.update(posix_group.model_dump())
                attributes["objectclass"].append("posixGroup")
                output.append(LDAPAttributeAdaptor(attributes))
            except ValidationError as exc:
                name = group_dict["cn"] if "cn" in group_dict else "unknown"
                log.msg(f"Validation failed for group '{name}'.")
                for error in exc.errors():
                    log.msg(
                        f"... '{error['loc'][0]}': {error['msg']} but '{error['input']}' was provided."
                    )
        return output

    def validated_users(self) -> list[LDAPAttributeAdaptor]:
        """
        Validate output via pydantic and return a list of LDAPAttributeAdaptor
        """
        if self.debug:
            log.msg("Constructing and validating list of users")
        output = []
        for user_dict in self.users():
            try:
                attributes = {"objectclass": ["top"]}
                # Add user to self-titled group
                user_dict["memberOf"].append(
                    f"CN={user_dict['cn']},OU=groups,{self.root_dn}"
                )
                # Add 'inetOrgPerson' attributes
                inetorg_person = LDAPInetOrgPerson(**user_dict)
                attributes.update(inetorg_person.model_dump())
                attributes["objectclass"].append("inetOrgPerson")
                # Add 'inetUser' attributes
                inet_user = LDAPInetUser(**user_dict)
                attributes.update(inet_user.model_dump())
                attributes["objectclass"].append("inetuser")
                # Add 'person' attributes
                person = LDAPPerson(**user_dict)
                attributes.update(person.model_dump())
                attributes["objectclass"].append("person")
                # Add 'posixAccount' attributes
                posix_account = LDAPPosixAccount(**user_dict)
                attributes.update(posix_account.model_dump())
                attributes["objectclass"].append("posixAccount")
                # Add 'OAuthUser' attributes
                oauth_user = LDAPOAuthUser(**user_dict)
                attributes.update(oauth_user.model_dump())
                attributes["objectclass"].append("oauthUser")
                output.append(LDAPAttributeAdaptor(attributes))
            except ValidationError as exc:
                name = user_dict["cn"] if "cn" in user_dict else "unknown"
                log.msg(f"Validation failed for user '{name}'.")
                for error in exc.errors():
                    log.msg(
                        f"... '{error['loc'][0]}': {error['msg']} but '{error['input']}' was provided."
                    )
        return output

    def verify(self, username: str, password: str) -> bool:
        """Verify client connection details"""
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
