from typing import Any, cast

from apricot.types import JSONDict

from .oauth_client import OAuthClient


def get_single_value_attribute(obj: JSONDict, key: str, default=None) -> Any:
    for part in key.split("."):
        obj = obj.get(part)
        if obj is None:
            return default
    if isinstance(obj, list):
        try:
            return next(iter(obj))
        except StopIteration:
            pass
    else:
        return obj
    return default


class KeycloakClient(OAuthClient):
    """OAuth client for the Keycloak backend."""

    max_rows = 100

    def __init__(
        self,
        keycloak_base_url: str,
        keycloak_realm: str,
        **kwargs: Any,
    ):
        self.base_url = keycloak_base_url
        self.realm = keycloak_realm

        redirect_uri = "urn:ietf:wg:oauth:2.0:oob"  # this is the "no redirect" URL
        scopes = []  # this is the default scope
        token_url = (
            f"{self.base_url}/realms/{self.realm}/protocol/openid-connect/token"
        )

        super().__init__(
            redirect_uri=redirect_uri, scopes=scopes, token_url=token_url, **kwargs,
        )

    def extract_token(self, json_response: JSONDict) -> str:
        return str(json_response["access_token"])

    def groups(self) -> list[JSONDict]:
        output = []
        try:
            group_data = []
            while data := self.query(
                f"{self.base_url}/admin/realms/{self.realm}/groups?first={len(group_data)}&max={self.max_rows}&briefRepresentation=false"
            ):
                group_data.extend(data)
                if len(data) != self.max_rows:
                    break

            group_data = sorted(group_data, key=lambda g: int(get_single_value_attribute(g, "attributes.gid", default="9999999999"), 10))

            next_gid = max(
                *(
                    int(get_single_value_attribute(g, "attributes.gid", default="-1"), 10)+1
                    for g in group_data
                ),
                3000
            )

            for group_dict in cast(
                list[JSONDict],
                group_data,
            ):
                group_gid = get_single_value_attribute(group_dict, "attributes.gid", default=None)
                if group_gid:
                    group_gid = int(group_gid, 10)
                if not group_gid:
                    group_gid = next_gid
                    next_gid += 1
                    group_dict["attributes"] = group_dict.get("attributes", {})
                    group_dict["attributes"]["gid"] = [str(group_gid)]
                    self.request(
                        f"{self.base_url}/admin/realms/{self.realm}/groups/{group_dict['id']}",
                        method="PUT",
                        json=group_dict
                    )
                attributes: JSONDict = {}
                attributes["cn"] = group_dict.get("name", None)
                attributes["description"] = group_dict.get("id", None)
                attributes["gidNumber"] = group_gid
                attributes["oauth_id"] = group_dict.get("id", None)
                # Add membership attributes
                members = self.query(
                    f"{self.base_url}/admin/realms/{self.realm}/groups/{group_dict['id']}/members"
                )
                attributes["memberUid"] = [
                    user["username"]
                    for user in cast(list[JSONDict], members)
                ]
                output.append(attributes)
        except KeyError:
            pass
        return output

    def users(self) -> list[JSONDict]:
        output = []
        try:
            user_data = []
            while data := self.query(
                f"{self.base_url}/admin/realms/{self.realm}/users?first={len(user_data)}&max={self.max_rows}&briefRepresentation=false"
            ):
                user_data.extend(data)
                if len(data) != self.max_rows:
                    break

            user_data = sorted(user_data, key=lambda u: int(get_single_value_attribute(u, "attributes.uid", default="9999999999"), 10))

            next_uid = max(
                *(
                    int(get_single_value_attribute(g, "attributes.uid", default="-1"), 10)+1
                    for g in user_data
                ),
                3000
            )

            for user_dict in cast(
                list[JSONDict],
                sorted(user_data, key=lambda user: user["createdTimestamp"]),
            ):
                user_uid = get_single_value_attribute(user_dict, "attributes.uid", default=None)
                if user_uid:
                    user_uid = int(user_uid, 10)
                if not user_uid:
                    user_uid = next_uid
                    next_uid += 1

                    user_dict["attributes"] = user_dict.get("attributes", {})
                    user_dict["attributes"]["uid"] = [str(user_uid)]
                    self.request(
                        f"{self.base_url}/admin/realms/{self.realm}/users/{user_dict['id']}",
                        method="PUT",
                        json=user_dict
                    )
                # Get user attributes
                first_name = user_dict.get("firstName", None)
                last_name = user_dict.get("lastName", None)
                full_name = " ".join(filter(lambda x: x, [first_name, last_name])) or None
                username = user_dict.get("username")
                attributes: JSONDict = {}
                attributes["cn"] = username
                attributes["uid"] = username
                attributes["oauth_username"] = username
                attributes["displayName"] = full_name
                attributes["mail"] = user_dict.get("email")
                attributes["description"] = ""
                attributes["gidNumber"] = user_uid
                attributes["givenName"] = first_name if first_name else ""
                attributes["homeDirectory"] = f"/home/{username}" if username else None
                attributes["oauth_id"] = user_dict.get("id", None)
                attributes["sn"] = last_name if last_name else ""
                attributes["uidNumber"] = user_uid
                output.append(attributes)
        except KeyError:
            pass
        return output
