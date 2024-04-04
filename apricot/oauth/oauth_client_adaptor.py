from abc import abstractmethod
from collections.abc import Sequence
from typing import Any

from pydantic import BaseModel, ValidationError
from twisted.python import log

from apricot.models import (
    LDAPAttributeAdaptor,
    LDAPGroupOfNames,
    LDAPInetOrgPerson,
    LDAPOAuthUser,
    LDAPPosixAccount,
    LDAPPosixGroup,
)

from .oauth_client import OAuthClient


class OAuthClientAdaptor(OAuthClient):
    """Adaptor for converting raw user and group data into LDAP format."""

    def __init__(self, **kwargs: Any):
        self.ldap_groups: list[LDAPAttributeAdaptor] = []
        self.ldap_users: list[LDAPAttributeAdaptor] = []
        super().__init__(**kwargs)

    @abstractmethod
    def unvalidated_groups(self) -> list[dict[str, Any]]:
        """
        Return a list of group data

        Each return value should be a dict where 'None' is used to signify a missing value
        """
        pass

    @abstractmethod
    def unvalidated_users(self) -> list[dict[str, Any]]:
        """
        Return a list of user data

        Each return value should be a dict where 'None' is used to signify a missing value
        """
        pass

    def group_dn_from_cn(self, group_cn: str) -> str:
        return f"CN={group_cn},OU=groups,{self.root_dn}"

    def user_dn_from_cn(self, user_cn: str) -> str:
        return f"CN={user_cn},OU=users,{self.root_dn}"

    def construct_user_primary_groups(self) -> list[dict[str, Any]]:
        """
        Each user needs a self-titled primary group
        """
        # Add one self-titled group for each user
        user_group_dicts = []
        for user_dict in list(self.unvalidated_users()):
            user_dict["memberUid"] = [user_dict["uid"]]
            user_dict["member"] = [self.user_dn_from_cn(user_dict["cn"])]
            # Group name is taken from 'cn' which should match the username
            user_dict["cn"] = user_dict["uid"]
            user_group_dicts.append(user_dict)
        return user_group_dicts

    def groups(self) -> list[LDAPAttributeAdaptor]:
        return self.ldap_groups

    def users(self) -> list[LDAPAttributeAdaptor]:
        return self.ldap_users

    def refresh(self) -> None:
        self.ldap_groups = self.refresh_groups()
        self.ldap_users = self.refresh_users()

    def refresh_groups(self) -> list[LDAPAttributeAdaptor]:
        """
        Validate output via pydantic and return a list of LDAPAttributeAdaptor
        """
        if self.debug:
            log.msg("Constructing and validating list of groups")
        output = []
        # Add one self-titled group for each user
        user_primary_groups = self.construct_user_primary_groups()
        # Iterate over groups and validate them
        for group_dict in self.unvalidated_groups() + user_primary_groups:
            try:
                attributes = {"objectclass": ["top"]}
                # Add appropriate LDAP class attributes
                for ldap_class in self.ldap_group_classes:
                    model = ldap_class(**group_dict)
                    attributes.update(model.model_dump())
                    attributes["objectclass"] += model.names()
                output.append(LDAPAttributeAdaptor(attributes))
            except ValidationError as exc:
                name = group_dict["cn"] if "cn" in group_dict else "unknown"
                log.msg(f"Validation failed for group '{name}'.")
                for error in exc.errors():
                    log.msg(
                        f"... '{error['loc'][0]}': {error['msg']} but '{error['input']}' was provided."
                    )
        return output

    def refresh_users(self) -> list[LDAPAttributeAdaptor]:
        """
        Validate output via pydantic and return a list of LDAPAttributeAdaptor
        """
        if self.debug:
            log.msg("Constructing and validating list of users")
        output = []
        for user_dict in list(self.unvalidated_users()):
            try:
                attributes = {"objectclass": ["top"]}
                # Add user to self-titled group
                user_dict["memberOf"].append(self.group_dn_from_cn(user_dict["cn"]))
                # Add appropriate LDAP class attributes
                for ldap_class in self.ldap_user_classes:
                    model = ldap_class(**user_dict)
                    attributes.update(model.model_dump())
                    attributes["objectclass"] += model.names()
                output.append(LDAPAttributeAdaptor(attributes))
            except ValidationError as exc:
                name = user_dict["cn"] if "cn" in user_dict else "unknown"
                log.msg(f"Validation failed for user '{name}'.")
                for error in exc.errors():
                    log.msg(
                        f"... '{error['loc'][0]}': {error['msg']} but '{error['input']}' was provided."
                    )
        return output
