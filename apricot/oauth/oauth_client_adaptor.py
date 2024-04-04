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


class OAuthClientAdaptor(OAuthClient):
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
            log.msg("Constructing and validating list of groups")
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
        Obtain lists of users and groups.
        """
        # Get the unvalidated users and groups
        _groups = self.unvalidated_groups()
        _users = self.unvalidated_users()

        # Add one self-titled group for each user
        # Group name is taken from 'cn' which should match the username
        user_primary_groups = []
        for user in _users:
            group_dict = {}
            for attr in ("cn", "description", "gidNumber"):
                group_dict[attr] = user[attr]
            group_dict["member"] = [self.user_dn_from_cn(user["cn"])]
            group_dict["memberUid"] = [user["uid"]]
            user_primary_groups.append(group_dict)

        self.group_dicts = _groups + user_primary_groups
        self.user_dicts = _users

    def users(self) -> list[LDAPAttributeAdaptor]:
        """
        Validate output with pydantic and return a list of LDAPAttributeAdaptor
        """
        if self.debug:
            log.msg("Constructing and validating list of users")
        output = []
        for user_dict in self.user_dicts:
            try:
                # Add user to self-titled group
                user_dict["memberOf"].append(self.group_dn_from_cn(user_dict["cn"]))
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
