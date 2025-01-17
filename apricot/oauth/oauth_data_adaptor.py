from __future__ import annotations

from typing import TYPE_CHECKING, Self

from pydantic import ValidationError
from twisted.logger import Logger

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

    from apricot.typedefs import JSONDict

    from .oauth_client import OAuthClient


class OAuthDataAdaptor:
    """Adaptor for converting raw user and group data into LDAP format."""

    def __init__(
        self: Self,
        domain: str,
        oauth_client: OAuthClient,
        *,
        enable_mirrored_groups: bool,
        enable_primary_groups: bool,
        enable_user_domain_verification: bool,
    ) -> None:
        """Initialise an OAuthDataAdaptor.

        Args:
            domain: The root domain of the LDAP tree
            enable_mirrored_groups: Whether to create a mirrored LDAP group-of-groups
                for each group-of-users
            enable_primary_groups: Whether to create an LDAP primary group for each user
            enable_user_domain_verification: Whether to verify users belong to the
                correct domain
            oauth_client: An OAuth client used to construct the LDAP tree
        """
        self.domain = domain
        self.enable_mirrored_groups = enable_mirrored_groups
        self.enable_primary_groups = enable_primary_groups
        self.enable_user_domain_verification = enable_user_domain_verification
        self.logger = Logger()
        self.oauth_client = oauth_client
        self.root_dn = "DC=" + domain.replace(".", ",DC=")

    def _dn_from_group_cn(self: Self, group_cn: str) -> str:
        return f"CN={group_cn},OU=groups,{self.root_dn}"

    def _dn_from_user_cn(self: Self, user_cn: str) -> str:
        return f"CN={user_cn},OU=users,{self.root_dn}"

    def _retrieve_entries(  # noqa: C901
        self: Self,
    ) -> tuple[
        list[tuple[JSONDict, list[type[LDAPObjectClass]]]],
        list[tuple[JSONDict, list[type[LDAPObjectClass]]]],
    ]:
        """Obtain lists of users and groups, and construct necessary meta-entries.

        Returns:
            Two lists, one for users and one for groups. Each list consists of tuples
            representing object information in JSON format, together with a list of LDAP
            object classes that should be used to validate this object.
        """
        # Get the initial set of users and groups
        oauth_groups = self.oauth_client.groups()
        oauth_users = self.oauth_client.users()
        self.logger.debug(
            "Loaded {n_groups} groups and {n_users} users from OAuth client.",
            n_groups=len(oauth_groups),
            n_users=len(oauth_users),
        )

        # Ensure member is set for groups
        for group_dict in oauth_groups:
            group_dict["member"] = [
                self._dn_from_user_cn(user_cn) for user_cn in group_dict["memberUid"]
            ]

        # Add one self-titled primary group for each user
        # Group name is taken from 'cn' which should match the username
        user_primary_groups = []
        if self.enable_primary_groups:
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
        if self.enable_primary_groups and self.enable_mirrored_groups:
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
            for group_name in child_dict["memberOf"]:
                self.logger.debug(
                    "... user '{user}' is a member of '{group_name}'",
                    user=child_dict["cn"],
                    group_name=group_name,
                )

        # Ensure memberOf is set correctly for groups
        for child_dict in oauth_groups + user_primary_groups + groups_of_groups:
            child_dn = self._dn_from_group_cn(child_dict["cn"])
            child_dict["memberOf"] = [
                self._dn_from_group_cn(parent_dict["cn"])
                for parent_dict in oauth_groups + user_primary_groups + groups_of_groups
                if child_dn in parent_dict["member"]
            ]
            for group_name in child_dict["memberOf"]:
                self.logger.debug(
                    "... group '{group}' is a member of '{group_name}'",
                    group=child_dict["cn"],
                    group_name=group_name,
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
        """Validate a list of groups.

        Args:
            annotated_groups: a list of groups to validate

        Returns:
            A list with one LDAPAttributeAdaptor for each valid group
        """
        self.logger.debug(
            "Attempting to validate {n_groups} groups.",
            n_groups=len(annotated_groups),
        )
        output = []
        for group_dict, required_classes in annotated_groups:
            try:
                output.append(
                    LDAPAttributeAdaptor.from_attributes(
                        group_dict,
                        required_classes=required_classes,
                    ),
                )
            except ValidationError as exc:  # noqa: PERF203
                self.logger.warn(
                    "... group '{group_name}' failed validation.",
                    group_name=group_dict.get("cn", "unknown"),
                )
                for error in exc.errors():
                    self.logger.warn(
                        " -> '{attribute}': {expected} but '{actual}' was provided.",
                        attribute=error["loc"][0],
                        expected=error["msg"],
                        actual=error["input"],
                    )

        return output

    def _validate_users(
        self: Self,
        annotated_users: list[tuple[JSONDict, list[type[LDAPObjectClass]]]],
    ) -> list[LDAPAttributeAdaptor]:
        """Validate a list of users.

        Args:
            annotated_users: a list of users to validate

        Returns:
            A list with one LDAPAttributeAdaptor for each valid user
        """
        self.logger.debug(
            "Attempting to validate {n_users} users.",
            n_users=len(annotated_users),
        )
        output = []
        for user_dict, required_classes in annotated_users:
            try:
                # Verify user domain if enabled
                if (
                    self.enable_user_domain_verification
                    and (user_domain := user_dict.get("domain", None)) != self.domain
                ):
                    self.logger.warn(
                        "... user '{user_name}' failed validation.",
                        user_name=user_dict.get("cn", "unknown"),
                    )
                    self.logger.warn(
                        " -> 'domain': expected '{expected_domain}' but '{actual_domain}' was provided.",  # noqa: E501
                        expected_domain=self.domain,
                        actual_domain=user_domain,
                    )
                    continue
                # Construct an LDAPAttributeAdaptor from the user attributes
                output.append(
                    LDAPAttributeAdaptor.from_attributes(
                        user_dict,
                        required_classes=required_classes,
                    ),
                )
            except ValidationError as exc:
                self.logger.warn(
                    "... user '{user_name}' failed validation.",
                    user_name=user_dict.get("cn", "unknown"),
                )
                for error in exc.errors():
                    self.logger.warn(
                        " -> '{attribute}': {expected} but '{actual}' was provided.",
                        attribute=error["loc"][0],
                        expected=error["msg"],
                        actual=error["input"],
                    )
        return output

    def retrieve_all(
        self,
    ) -> tuple[list[LDAPAttributeAdaptor], list[LDAPAttributeAdaptor]]:
        """Retrieve validated user and group information.

        Returns:
            A tuple of groups and users
        """
        annotated_groups, annotated_users = self._retrieve_entries()
        validated_groups = self._validate_groups(annotated_groups)
        validated_users = self._validate_users(annotated_users)
        self.logger.debug(
            "Validated {n_groups} groups and {n_users} users.",
            n_groups=len(validated_groups),
            n_users=len(validated_users),
        )
        return (validated_groups, validated_users)
