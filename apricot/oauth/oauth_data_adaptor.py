from abc import abstractmethod
from collections.abc import Sequence
from typing import Any

from pydantic import ValidationError
from twisted.python import log

from apricot.models import (
    LDAPAttributeAdaptor,
    LDAPGroupOfNames,
    LDAPInetOrgPerson,
    LDAPPosixAccount,
    LDAPPosixGroup,
    NamedLDAPClass,
    OverlayMemberOf,
    OverlayOAuthEntry,
)
from apricot.types import JSONDict

from .oauth_client import OAuthClient


class OAuthDataAdaptor(OAuthClient):
    """Adaptor for converting raw user and group data into LDAP format."""

    def __init__(self, **kwargs: Any):
        self.group_dicts: list[JSONDict] = []
        self.user_dicts: list[JSONDict] = []
        super().__init__(**kwargs)

    @abstractmethod
    def unvalidated_groups(self) -> list[JSONDict]:
        """
        Return a list of group data

        Each return value should be a dict where 'None' is used to signify a missing value
        """
        pass

    @abstractmethod
    def unvalidated_users(self) -> list[JSONDict]:
        """
        Return a list of user data

        Each return value should be a dict where 'None' is used to signify a missing value
        """
        pass

    def extract_attributes(
        self,
        input_dict: JSONDict,
        required_classes: Sequence[type[NamedLDAPClass]],
        optional_classes: Sequence[type[NamedLDAPClass]],
    ) -> LDAPAttributeAdaptor:
        """Add appropriate LDAP class attributes"""
        attributes = {"objectclass": ["top"]}
        # Add required attributes
        for ldap_class in required_classes:
            model = ldap_class(**input_dict)
            attributes.update(model.model_dump())
            attributes["objectclass"] += model.names()
        # Attempt to add optional attributes
        try:
            for ldap_class in optional_classes:
                model = ldap_class(**input_dict)
                attributes.update(model.model_dump())
                attributes["objectclass"] += model.names()
        except ValidationError:
            if self.debug:
                log.msg(f"Could not parse input as a valid '{ldap_class.__name__}'.")
        return LDAPAttributeAdaptor(attributes)

    def groups(self) -> list[LDAPAttributeAdaptor]:
        """
        Validate output with pydantic and return a list of LDAPAttributeAdaptor
        """
        if self.debug:
            log.msg("Constructing and validating list of groups.")
        output = []
        for group_dict in self.group_dicts:
            try:
                output.append(
                    self.extract_attributes(
                        group_dict,
                        required_classes=[LDAPGroupOfNames, OverlayMemberOf],
                        optional_classes=[LDAPPosixGroup, OverlayOAuthEntry],
                    )
                )
            except ValidationError as exc:
                name = group_dict["cn"] if "cn" in group_dict else "unknown"
                log.msg(f"Validation failed for group '{name}'.")
                for error in exc.errors():
                    log.msg(
                        f"... '{error['loc'][0]}': {error['msg']} but '{error['input']}' was provided."
                    )
        return output

    def refresh(self) -> None:
        """
        Obtain lists of users and groups, and construct necessary meta-entries.
        """
        # Get the unvalidated users and groups
        _groups = self.unvalidated_groups()
        _users = self.unvalidated_users()

        # Ensure member is set for groups
        for group_dict in _groups:
            group_dict["member"] = [
                self.user_dn_from_cn(user["cn"]) for user in group_dict["memberUid"]
            ]

        # Add one self-titled group for each user
        # Group name is taken from 'cn' which should match the username
        user_primary_groups = []
        for user in _users:
            group_dict = {}
            for attr in ("cn", "description", "gidNumber"):
                group_dict[attr] = user[attr]
            group_dict["member"] = [self.user_dn_from_cn(user["cn"])]
            group_dict["memberUid"] = [user["cn"]]
            user_primary_groups.append(group_dict)

        # Add one group of groups for each existing group.
        # Its members are the primary user groups for each original group member.
        groups_of_groups = []
        for group in _groups:
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

        # Set overall group and user dicts
        self.group_dicts = _groups + user_primary_groups + groups_of_groups
        self.user_dicts = _users

        # Ensure memberOf is set correctly for users
        for child_dict in _users:
            child_dn = self.user_dn_from_cn(child_dict["cn"])
            child_dict["memberOf"] = [
                self.group_dn_from_cn(parent_dict["cn"])
                for parent_dict in self.group_dicts
                if child_dn in parent_dict["member"]
            ]

        # Ensure memberOf is set correctly for groups
        for child_dict in self.group_dicts:
            child_dn = self.group_dn_from_cn(child_dict["cn"])
            child_dict["memberOf"] = [
                self.group_dn_from_cn(parent_dict["cn"])
                for parent_dict in self.group_dicts
                if child_dn in parent_dict["member"]
            ]

    def users(self) -> list[LDAPAttributeAdaptor]:
        """
        Validate output with pydantic and return a list of LDAPAttributeAdaptor
        """
        if self.debug:
            log.msg("Constructing and validating list of users.")
        output = []
        for user_dict in self.user_dicts:
            try:
                output.append(
                    self.extract_attributes(
                        user_dict,
                        required_classes=[
                            LDAPInetOrgPerson,
                            LDAPPosixAccount,
                            OverlayMemberOf,
                            OverlayOAuthEntry,
                        ],
                        optional_classes=[],
                    )
                )
            except ValidationError as exc:
                name = user_dict["cn"] if "cn" in user_dict else "unknown"
                log.msg(f"Validation failed for user '{name}'.")
                for error in exc.errors():
                    log.msg(
                        f"... '{error['loc'][0]}': {error['msg']} but '{error['input']}' was provided."
                    )
        return output