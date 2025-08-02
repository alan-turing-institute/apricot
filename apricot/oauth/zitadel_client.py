from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING, Any, Self, override

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from apricot.oauth.oauth_client import OAuthClient

if TYPE_CHECKING:
    from apricot.typedefs import JSONDict


class ZitadelUser(BaseModel):
    """Zitadel user account information."""

    id: str
    display_name: str = Field(alias="displayName")
    preferred_login_name: str = Field(alias="preferredLoginName")


class ZitadelServiceUser(BaseModel):
    """Zitadel service user account information."""

    id: str
    preferred_login_name: str = Field(alias="preferredLoginName")


class ZitadelAuthorization(BaseModel):
    """Zitadel authorization mapping users to roles."""

    user: ZitadelUser | ZitadelServiceUser


class ZitadelRole(BaseModel):
    """Zitadel project role information."""

    key: str
    display_name: str = Field(alias="displayName")


class ZitadelPagination(BaseModel):
    """Zitadel API pagination metadata."""

    applied_limit: int = Field(alias="appliedLimit")


class ZitadelListAuthorizationsResponse(BaseModel):
    """Response from Zitadel authorization listing API."""

    model_config = ConfigDict(strict=True)

    pagination: ZitadelPagination
    authorizations: list[ZitadelAuthorization]


class ZitadelListProjectRolesResponse(BaseModel):
    """Response from Zitadel project roles listing API."""

    model_config = ConfigDict(strict=True)

    pagination: ZitadelPagination
    project_roles: list[ZitadelRole] = Field(alias="projectRoles")


COMMON_HEADERS = {
    "Connect-Protocol-Version": "1",
    "Content-Type": "application/json",
}
MAX_ROWS = 1000


class ZitadelClient(OAuthClient):
    """OAuth client for the Zitadel backend."""

    base_url: str
    project_id: str

    def __init__(
        self: Self,
        zitadel_base_url: str,
        zitadel_project_id: str,
        **kwargs: Any,
    ) -> None:
        """Initialise a ZitadelClient.

        Args:
            zitadel_base_url: Base URL for Zitadel server
            zitadel_project_id: Zitadel project ID
            kwargs: OAuthClient keyword arguments
        """
        self.base_url = zitadel_base_url
        self.project_id = zitadel_project_id

        redirect_uri = "urn:ietf:wg:oauth:2.0:oob"  # this is the "no redirect" URL
        scopes: list[str] = [
            # Zitadel requires _at least_ this scope.
            "openid",
            # This scope is needed to access the Zitadel API.
            "urn:zitadel:iam:org:project:id:zitadel:aud",
        ]
        token_url = f"{self.base_url}/oauth/v2/token"

        super().__init__(
            redirect_uri=redirect_uri,
            scopes_application=scopes,
            scopes_delegated=scopes,
            token_url=token_url,
            **kwargs,
        )

    @override
    @staticmethod
    def extract_token(json_response: JSONDict) -> str:
        return str(json_response["access_token"])

    @override
    def groups(self) -> list[JSONDict]:
        self.logger.info("Requesting groups")

        output: list[JSONDict] = []

        for role in self.project_roles():
            attributes: JSONDict = {}
            attributes["cn"] = role.display_name
            attributes["description"] = role.key
            attributes["gidNumber"] = self.uid_cache.get_group_uid(role.key)
            attributes["oauth_id"] = role.key

            attributes["memberUid"] = [
                authorization.user.preferred_login_name
                for authorization in self.authorizations(
                    role_key=role.key,
                )
            ]

            output.append(attributes)

        return output

    @override
    def users(self) -> list[JSONDict]:
        self.logger.info("Requesting users")

        output: list[JSONDict] = []

        for authorization in self.authorizations():
            attributes: JSONDict = {}

            if isinstance(authorization.user, ZitadelUser):
                full_name = authorization.user.display_name
            else:
                full_name = authorization.user.preferred_login_name

            username = authorization.user.preferred_login_name
            user_uid = self.uid_cache.get_user_uid(authorization.user.id)

            attributes["cn"] = username
            attributes["description"] = ""
            attributes["displayName"] = full_name
            attributes["domain"] = re.sub(r"https?://", "", self.base_url)
            attributes["gidNumber"] = user_uid
            attributes["homeDirectory"] = f"/home/{username}"
            attributes["oauth_id"] = authorization.user.id
            attributes["oauth_username"] = username
            attributes["sn"] = full_name
            attributes["uid"] = username
            attributes["uidNumber"] = user_uid

            output.append(attributes)

        return output

    def project_roles(self) -> list[ZitadelRole]:
        """Fetch all project roles from Zitadel."""
        roles: list[ZitadelRole] = []

        try:
            current_offset = 0
            while data := self.request(
                url=f"{self.base_url}/zitadel.project.v2beta.ProjectService/ListProjectRoles",
                method="POST",
                headers=COMMON_HEADERS,
                data=json.dumps(
                    {
                        "projectId": self.project_id,
                        "pagination": {
                            "offset": current_offset,
                            "limit": MAX_ROWS,
                        },
                    },
                ),
            ):
                self.logger.debug("Roles query {data}", data=data)

                data = ZitadelListProjectRolesResponse.model_validate(data)
                roles.extend(data.project_roles)

                if len(data.project_roles) < MAX_ROWS:
                    break

                current_offset += len(data.project_roles)
        except ValidationError as e:
            msg = f"Failed to parse Zitadel role search result: {e}"
            self.logger.error(msg)
            return []

        return roles

    def authorizations(
        self,
        *,
        role_key: str | None = None,
    ) -> list[ZitadelAuthorization]:
        """Fetch user authorizations from Zitadel.

        Args:
            role_key: Optional role key to filter authorizations
        """
        authorizations: list[ZitadelAuthorization] = []

        filters = [{"projectId": {"id": self.project_id}}]
        if role_key:
            filters.append({"roleKey": {"key": role_key}})

        try:
            current_offset = 0
            while data := self.request(
                url=f"{self.base_url}/zitadel.authorization.v2beta.AuthorizationService/ListAuthorizations",
                method="POST",
                headers=COMMON_HEADERS,
                data=json.dumps(
                    {
                        "pagination": {
                            "offset": current_offset,
                            "limit": MAX_ROWS,
                        },
                        "filters": filters,
                    },
                ),
            ):
                self.logger.debug("Role members query {data}", data=data)

                data = ZitadelListAuthorizationsResponse.model_validate(obj=data)
                authorizations.extend(data.authorizations)

                if len(data.authorizations) < MAX_ROWS:
                    break

                current_offset += len(data.authorizations)
        except ValidationError as e:
            msg = f"Failed to parse Zitadel role members search result: {e}"
            self.logger.error(msg)
            return []

        return authorizations
