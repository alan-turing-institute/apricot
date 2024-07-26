from __future__ import annotations

import operator
from typing import Any, Self, cast

from apricot.types import JSONDict

from .oauth_client import OAuthClient


class KeycloakClient(OAuthClient):
    """OAuth client for the Keycloak backend."""

    max_rows = 100

    def __init__(
        self: Self,
        keycloak_base_url: str,
        keycloak_realm: str,
        **kwargs: Any,
    ) -> None:
        """Initialise a KeycloakClient.

        @param keycloak_base_url: Base URL for Keycloak server
        @param keycloak_realm: Realm for Keycloak server
        """
        self.base_url = keycloak_base_url
        self.realm = keycloak_realm

        redirect_uri = "urn:ietf:wg:oauth:2.0:oob"  # this is the "no redirect" URL
        scopes: list[str] = []  # this is the default scope
        token_url = f"{self.base_url}/realms/{self.realm}/protocol/openid-connect/token"

        super().__init__(
            redirect_uri=redirect_uri,
            scopes_application=scopes,
            scopes_delegated=scopes,
            token_url=token_url,
            **kwargs,
        )

    @staticmethod
    def extract_token(json_response: JSONDict) -> str:
        return str(json_response["access_token"])

    def groups(self: Self) -> list[JSONDict]:
        output = []
        try:
            group_data: list[JSONDict] = []
            while data := self.query(
                f"{self.base_url}/admin/realms/{self.realm}/groups?first={len(group_data)}&max={self.max_rows}&briefRepresentation=false",
                use_client_secret=False,
            ):
                group_data.extend(cast(list[JSONDict], data))
                if len(data) != self.max_rows:
                    break

            # Ensure that gid attribute exists for all groups
            for group_dict in group_data:
                group_dict["attributes"] = group_dict.get("attributes", {})
                if "gid" not in group_dict["attributes"]:
                    group_dict["attributes"]["gid"] = None
                # If group_gid exists then set the cache to the same value
                # This ensures that any groups without a `gid` attribute will receive a
                # UID that does not overlap with existing groups
                if (group_gid := group_dict["attributes"]["gid"]) and len(
                    group_dict["attributes"]["gid"],
                ) == 1:
                    self.uid_cache.overwrite_group_uid(
                        group_dict["id"],
                        int(group_gid[0], 10),
                    )

            # Read group attributes
            for group_dict in group_data:
                if not group_dict["attributes"]["gid"]:
                    group_dict["attributes"]["gid"] = [
                        str(self.uid_cache.get_group_uid(group_dict["id"])),
                    ]
                    self.request(
                        f"{self.base_url}/admin/realms/{self.realm}/groups/{group_dict['id']}",
                        method="PUT",
                        json=group_dict,
                    )
                attributes: JSONDict = {}
                attributes["cn"] = group_dict.get("name", None)
                attributes["description"] = group_dict.get("id", None)
                attributes["gidNumber"] = group_dict["attributes"]["gid"][0]
                attributes["oauth_id"] = group_dict.get("id", None)
                # Add membership attributes
                members = self.query(
                    f"{self.base_url}/admin/realms/{self.realm}/groups/{group_dict['id']}/members",
                    use_client_secret=False,
                )
                attributes["memberUid"] = [
                    user["username"] for user in cast(list[JSONDict], members)
                ]
                output.append(attributes)
        except KeyError:
            pass
        return output

    def users(self: Self) -> list[JSONDict]:
        output = []
        try:
            user_data: list[JSONDict] = []
            while data := self.query(
                f"{self.base_url}/admin/realms/{self.realm}/users?first={len(user_data)}&max={self.max_rows}&briefRepresentation=false",
                use_client_secret=False,
            ):
                user_data.extend(cast(list[JSONDict], data))
                if len(data) != self.max_rows:
                    break

            # Ensure that uid attribute exists for all users
            for user_dict in user_data:
                user_dict["attributes"] = user_dict.get("attributes", {})
                if "uid" not in user_dict["attributes"]:
                    user_dict["attributes"]["uid"] = None
                # If user_uid exists then set the cache to the same value.
                # This ensures that any groups without a `gid` attribute will receive a
                # UID that does not overlap with existing groups
                if (user_uid := user_dict["attributes"]["uid"]) and len(
                    user_dict["attributes"]["uid"],
                ) == 1:
                    self.uid_cache.overwrite_user_uid(
                        user_dict["id"],
                        int(user_uid[0], 10),
                    )

            # Read user attributes
            for user_dict in sorted(
                user_data,
                key=operator.itemgetter("createdTimestamp"),
            ):
                if not user_dict["attributes"]["uid"]:
                    user_dict["attributes"]["uid"] = [
                        str(self.uid_cache.get_user_uid(user_dict["id"])),
                    ]
                    self.request(
                        f"{self.base_url}/admin/realms/{self.realm}/users/{user_dict['id']}",
                        method="PUT",
                        json=user_dict,
                    )
                # Get user attributes
                first_name = user_dict.get("firstName", None)
                last_name = user_dict.get("lastName", None)
                full_name = (
                    " ".join(filter(lambda x: x, [first_name, last_name])) or None
                )
                username = user_dict.get("username")
                attributes: JSONDict = {}
                attributes["cn"] = username
                attributes["uid"] = username
                attributes["oauth_username"] = username
                attributes["displayName"] = full_name
                attributes["mail"] = user_dict.get("email")
                attributes["description"] = ""
                attributes["gidNumber"] = user_dict["attributes"]["uid"][0]
                attributes["givenName"] = first_name or ""
                attributes["homeDirectory"] = f"/home/{username}" if username else None
                attributes["oauth_id"] = user_dict.get("id", None)
                attributes["sn"] = last_name or ""
                attributes["uidNumber"] = user_dict["attributes"]["uid"][0]
                output.append(attributes)
        except KeyError:
            pass
        return output
