from __future__ import annotations

import operator
from typing import TYPE_CHECKING, Any, Self, cast

from typing_extensions import override

from .oauth_client import OAuthClient

if TYPE_CHECKING:
    from apricot.typedefs import JSONDict


class MicrosoftEntraClient(OAuthClient):
    """OAuth client for the Microsoft Entra backend."""

    def __init__(
        self: Self,
        entra_tenant_id: str,
        **kwargs: Any,
    ) -> None:
        """Initialise a MicrosoftEntraClient.

        Args:
            entra_tenant_id: Tenant ID for the Entra ID
            kwargs: OAuthClient keyword arguments
        """
        redirect_uri = "urn:ietf:wg:oauth:2.0:oob"  # this is the "no redirect" URL
        token_url = (
            f"https://login.microsoftonline.com/{entra_tenant_id}/oauth2/v2.0/token"
        )
        # Use default application scope and minimal delegated scopes
        super().__init__(
            redirect_uri=redirect_uri,
            scopes_application=["https://graph.microsoft.com/.default"],
            scopes_delegated=["openid"],
            token_url=token_url,
            **kwargs,
        )

    @override
    @staticmethod
    def extract_token(json_response: JSONDict) -> str:
        return str(json_response["access_token"])

    @override
    def groups(self: Self) -> list[JSONDict]:
        output = []
        queries = [
            "createdDateTime",
            "displayName",
            "id",
        ]
        group_data: list[JSONDict] = []
        max_rows = 999
        current_query: str = (
            f"https://graph.microsoft.com/v1.0/groups?$select={','.join(queries)}&$top={max_rows}"
        )
        while response_data := self.query(current_query):
            self.logger.debug(
                "Retrieved group response object: {response}",
                response=response_data,
            )
            group_data.extend(cast("list[JSONDict]", response_data["value"]))
            if "@odata.nextLink" in response_data:
                current_query = response_data["@odata.nextLink"]
            else:
                break
        for group_dict in sorted(
            group_data,
            key=operator.itemgetter("createdDateTime"),
        ):
            try:
                group_uid = self.uid_cache.get_group_uid(group_dict["id"])
                attributes: JSONDict = {}
                attributes["cn"] = group_dict.get("displayName", None)
                attributes["description"] = group_dict.get("id", None)
                attributes["gidNumber"] = group_uid
                attributes["oauth_id"] = group_dict.get("id", None)
                # Add membership attributes
                members = self.query(
                    f"https://graph.microsoft.com/v1.0/groups/{group_dict['id']}/members",
                )
                attributes["memberUid"] = [
                    str(user["userPrincipalName"]).split("@")[0]
                    for user in members["value"]
                    if user.get("userPrincipalName")
                ]
                output.append(attributes)
            except KeyError as exc:  # noqa: PERF203
                self.logger.warn(
                    "Failed to process group {group} due to a missing key {key}.",
                    group=group_dict,
                    key=str(exc),
                )
        return output

    @override
    def users(self: Self) -> list[JSONDict]:
        output: list[JSONDict] = []
        current_query: str = ""
        try:
            queries = [
                "createdDateTime",
                "displayName",
                "givenName",
                "id",
                "surname",
                "userPrincipalName",
            ]
            max_rows = 999  # change this number to a much lower to go into development
            user_data: list[JSONDict] = []
            initial_query: str = (
                f"https://graph.microsoft.com/v1.0/users?$select={','.join(queries)}&$top={max_rows}"
            )
            current_query = initial_query
            while response_data := self.query(current_query):
                self.logger.debug(
                    "Retrieved user response object: {response}",
                    response=response_data,
                )
                user_data.extend(cast("list[JSONDict]", response_data["value"]))
                # @odata.nextLink - there is more data to retrieve
                if "@odata.nextLink" in response_data:
                    current_query = response_data["@odata.nextLink"]
                else:
                    break
            for user_dict in sorted(
                user_data,
                key=operator.itemgetter("createdDateTime"),
            ):
                # Get user attributes
                given_name = user_dict.get("givenName", None)
                surname = user_dict.get("surname", None)
                uid, domain = str(user_dict.get("userPrincipalName", "@")).split("@")
                user_uid = self.uid_cache.get_user_uid(user_dict["id"])
                attributes: JSONDict = {}
                attributes["cn"] = uid or None
                attributes["description"] = user_dict.get("displayName", None)
                attributes["displayName"] = user_dict.get("displayName", None)
                attributes["domain"] = domain
                attributes["gidNumber"] = user_uid
                attributes["givenName"] = given_name or ""
                attributes["homeDirectory"] = f"/home/{uid}" if uid else None
                attributes["oauth_id"] = user_dict.get("id", None)
                attributes["oauth_username"] = user_dict.get("userPrincipalName", None)
                attributes["sn"] = surname or ""
                attributes["uid"] = uid or None
                attributes["uidNumber"] = user_uid
                output.append(attributes)

        except KeyError as exc:
            self.logger.warn(
                "Failed to process user {user} due to a missing key {key}.",
                user=user_dict,
                key=str(exc),
            )
        return output
