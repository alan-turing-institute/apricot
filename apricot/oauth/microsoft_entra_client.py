from typing import Any, cast

from .oauth_client import OAuthClient
from .types import JSONDict


class MicrosoftEntraClient(OAuthClient):
    """OAuth client for the Microsoft Entra backend."""

    def __init__(
        self,
        entra_tenant_id: str,
        **kwargs: Any,
    ):
        redirect_uri = "urn:ietf:wg:oauth:2.0:oob"  # this is the "no redirect" URL
        scopes = ["https://graph.microsoft.com/.default"]  # this is the default scope
        token_url = (
            f"https://login.microsoftonline.com/{entra_tenant_id}/oauth2/v2.0/token"
        )
        self.tenant_id = entra_tenant_id
        super().__init__(
            redirect_uri=redirect_uri, scopes=scopes, token_url=token_url, **kwargs
        )

    def extract_token(self, json_response: JSONDict) -> str:
        return str(json_response["access_token"])

    def groups(self) -> list[dict[str, Any]]:
        output = []
        try:
            queries = [
                "createdDateTime",
                "displayName",
                "id",
            ]
            group_data = self.query(
                f"https://graph.microsoft.com/v1.0/groups?$select={','.join(queries)}"
            )
            for group_dict in cast(
                list[dict[str, Any]],
                sorted(group_data["value"], key=lambda group: group["createdDateTime"]),
            ):
                group_uid = self.uid_cache.get_group_uid(group_dict["id"])
                attributes = {}
                attributes["cn"] = group_dict.get("displayName", None)
                attributes["description"] = group_dict.get("id", None)
                attributes["gidNumber"] = group_uid
                # Add membership attributes
                members = self.query(
                    f"https://graph.microsoft.com/v1.0/groups/{group_dict['id']}/members"
                )
                attributes["memberUid"] = [
                    str(user["userPrincipalName"]).split("@")[0]
                    for user in members["value"]
                    if user["userPrincipalName"]
                ]
                attributes["member"] = [
                    f"CN={uid},OU=users,{self.root_dn}"
                    for uid in attributes["memberUid"]
                ]
                output.append(attributes)
        except KeyError:
            pass
        return output

    def users(self) -> list[dict[str, Any]]:
        output = []
        try:
            queries = [
                "createdDateTime",
                "displayName",
                "givenName",
                "id",
                "surname",
                "userPrincipalName",
            ]
            user_data = self.query(
                f"https://graph.microsoft.com/v1.0/users?$select={','.join(queries)}"
            )
            for user_dict in cast(
                list[dict[str, Any]],
                sorted(user_data["value"], key=lambda user: user["createdDateTime"]),
            ):
                # Get user attributes
                uid, domain = str(user_dict.get("userPrincipalName", "@")).split("@")
                user_uid = self.uid_cache.get_user_uid(user_dict["id"])
                attributes = {}
                attributes["cn"] = user_dict.get("displayName", None)
                attributes["description"] = user_dict.get("id", None)
                attributes["displayName"] = attributes.get("cn", None)
                attributes["domain"] = domain
                attributes["gidNumber"] = user_uid
                attributes["givenName"] = user_dict.get("givenName", "")
                attributes["homeDirectory"] = f"/home/{uid}" if uid else None
                attributes["sn"] = user_dict.get("surname", "")
                attributes["uid"] = uid if uid else None
                attributes["uidNumber"] = user_uid
                # Add group attributes
                group_memberships = self.query(
                    f"https://graph.microsoft.com/v1.0/users/{user_dict['id']}/memberOf"
                )
                attributes["memberOf"] = [
                    f"CN={group['displayName']},OU=groups,{self.root_dn}"
                    for group in group_memberships["value"]
                    if group["displayName"]
                ]
                output.append(attributes)
        except KeyError:
            pass
        return output
