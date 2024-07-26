from __future__ import annotations

from typing import TYPE_CHECKING, Self

from pydantic import ValidationError
from twisted.python import log

from apricot.models import (
    LDAPAttributeAdaptor,
    LDAPGroupOfNames,
    LDAPInetOrgPerson,
    LDAPObjectClass,
    LDAPPosixAccount,
    LDAPPosixGroup,
    OverlayMemberOf,
    OverlayOAuthEntry,
)

if TYPE_CHECKING:

    from apricot.types import JSONDict

    from .oauth_client import OAuthClient


class OAuthDataAdaptor:
    """Adaptor for converting raw user and group data into LDAP format."""

    def __init__(
        self: Self,
        domain: str,
        oauth_client: OAuthClient,
        *,
        enable_mirrored_groups: bool,
    ) -> None:
        """Initialise an OAuthDataAdaptor.

        @param domain: The root domain of the LDAP tree
        @param enable_mirrored_groups: Create a mirrored LDAP group-of-groups for each group-of-users
        @param oauth_client: An OAuth client used to construct the LDAP tree
        """
        self.debug = oauth_client.debug
        self.oauth_client = oauth_client
        self.root_dn = "DC=" + domain.replace(".", ",DC=")
        self.enable_mirrored_groups = enable_mirrored_groups

        # Retrieve and validate user and group information
        annotated_groups, annotated_users = self._retrieve_entries()
        self.validated_groups = self._validate_groups(annotated_groups)
        self.validated_users = self._validate_users(annotated_users, domain)
        if self.debug:
            log.msg(
                f"Validated {len(self.validated_groups)} groups and {len(self.validated_users)} users.",
            )

    @property
    def groups(self: Self) -> list[LDAPAttributeAdaptor]:
        """Return a list of LDAPAttributeAdaptors representing validated group data."""
        return self.validated_groups

    @property
    def users(self: Self) -> list[LDAPAttributeAdaptor]:
        """Return a list of LDAPAttributeAdaptors representing validated user data."""
        return self.validated_users

    def _dn_from_group_cn(self: Self, group_cn: str) -> str:
        return f"CN={group_cn},OU=groups,{self.root_dn}"

    def _dn_from_user_cn(self: Self, user_cn: str) -> str:
        return f"CN={user_cn},OU=users,{self.root_dn}"

    def _retrieve_entries(
        self: Self,
    ) -> tuple[
        list[tuple[JSONDict, list[type[LDAPObjectClass]]]],
        list[tuple[JSONDict, list[type[LDAPObjectClass]]]],
    ]:
        """Obtain lists of users and groups, and construct necessary meta-entries."""
        # Get the initial set of users and groups
        oauth_groups = self.oauth_client.groups()
        oauth_users = self.oauth_client.users()
        if self.debug:
            log.msg(
                f"Loaded {len(oauth_groups)} groups and {len(oauth_users)} users from OAuth client.",
            )

        # Ensure member is set for groups
        for group_dict in oauth_groups:
            group_dict["member"] = [
                self._dn_from_user_cn(user_cn) for user_cn in group_dict["memberUid"]
            ]

        # Add one self-titled group for each user
        # Group name is taken from 'cn' which should match the username
        user_primary_groups = []
        for user in oauth_users:
            group_dict = {}
            for attr in ("cn", "description", "gidNumber"):
                group_dict[attr] = user[attr]
            group_dict["member"] = [self._dn_from_user_cn(user["cn"])]
            group_dict["memberUid"] = [user["cn"]]
            user_primary_groups.append(group_dict)

        # Add one group of groups for each existing group.
        # Its members are the primary user groups for each original group member.
        groups_of_groups = []
        if self.enable_mirrored_groups:
            for group in oauth_groups:
                group_dict = {}
                group_dict["cn"] = f"Primary user groups for {group['cn']}"
                group_dict["description"] = (
                    f"Primary user groups for members of '{group['cn']}'"
                )
                # Replace each member user with a member group
                group_dict["member"] = [
                    str(member).replace("OU=users", "OU=groups")
                    for member in group["member"]
                ]
                # Groups do not have UIDs so memberUid must be empty
                group_dict["memberUid"] = []
                groups_of_groups.append(group_dict)

        # Ensure memberOf is set correctly for users
        for child_dict in oauth_users:
            child_dn = self._dn_from_user_cn(child_dict["cn"])
            child_dict["memberOf"] = [
                self._dn_from_group_cn(parent_dict["cn"])
                for parent_dict in oauth_groups + user_primary_groups + groups_of_groups
                if child_dn in parent_dict["member"]
            ]
            if self.debug:
                for group_name in child_dict["memberOf"]:
                    log.msg(
                        f"... user '{child_dict['cn']}' is a member of '{group_name}'",
                    )

        # Ensure memberOf is set correctly for groups
        for child_dict in oauth_groups + user_primary_groups + groups_of_groups:
            child_dn = self._dn_from_group_cn(child_dict["cn"])
            child_dict["memberOf"] = [
                self._dn_from_group_cn(parent_dict["cn"])
                for parent_dict in oauth_groups + user_primary_groups + groups_of_groups
                if child_dn in parent_dict["member"]
            ]
            if self.debug:
                for group_name in child_dict["memberOf"]:
                    log.msg(
                        f"... group '{child_dict['cn']}' is a member of '{group_name}'",
                    )

        # Annotate group and user dicts with the appropriate LDAP classes
        annotated_groups = [
            (
                group,
                [LDAPGroupOfNames, LDAPPosixGroup, OverlayMemberOf, OverlayOAuthEntry],
            )
            for group in oauth_groups
        ]
        annotated_groups += [
            (group, [LDAPGroupOfNames, LDAPPosixGroup, OverlayMemberOf])
            for group in user_primary_groups
        ]
        annotated_groups += [
            (group, [LDAPGroupOfNames, OverlayMemberOf]) for group in groups_of_groups
        ]
        annotated_users = [
            (
                user,
                [
                    LDAPInetOrgPerson,
                    LDAPPosixAccount,
                    OverlayMemberOf,
                    OverlayOAuthEntry,
                ],
            )
            for user in oauth_users
        ]
        return (annotated_groups, annotated_users)

    def _validate_groups(
        self: Self,
        annotated_groups: list[tuple[JSONDict, list[type[LDAPObjectClass]]]],
    ) -> list[LDAPAttributeAdaptor]:
        """Return a list of LDAPAttributeAdaptors representing validated group data."""
        if self.debug:
            log.msg(f"Attempting to validate {len(annotated_groups)} groups.")
        output = []
        for group_dict, required_classes in annotated_groups:
            try:
                output.append(
                    LDAPAttributeAdaptor.from_attributes(
                        group_dict,
                        required_classes=required_classes,
                    ),
                )
            except ValidationError as exc:
                name = group_dict.get("cn", "unknown")
                log.msg(f"... group '{name}' failed validation.")
                for error in exc.errors():
                    log.msg(
                        f" -> '{error['loc'][0]}': {error['msg']} but '{error['input']}' was provided.",
                    )
        return output

    def _validate_users(
        self: Self,
        annotated_users: list[tuple[JSONDict, list[type[LDAPObjectClass]]]],
        domain: str,
    ) -> list[LDAPAttributeAdaptor]:
        """Return a list of LDAPAttributeAdaptors representing validated user data."""
        if self.debug:
            log.msg(f"Attempting to validate {len(annotated_users)} users.")
        output = []
        for user_dict, required_classes in annotated_users:
            name = user_dict.get("cn", "unknown")
            try:
                if (user_domain := user_dict.get("domain", None)) == domain:
                    output.append(
                        LDAPAttributeAdaptor.from_attributes(
                            user_dict,
                            required_classes=required_classes,
                        ),
                    )
                else:
                    log.msg(f"... user '{name}' failed validation.")
                    log.msg(
                        f" -> 'domain': expected '{domain}' but '{user_domain}' was provided.",
                    )
            except ValidationError as exc:
                log.msg(f"... user '{name}' failed validation.")
                for error in exc.errors():
                    log.msg(
                        f" -> '{error['loc'][0]}': {error['msg']} but '{error['input']}' was provided.",
                    )
        return output
