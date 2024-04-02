from abc import abstractmethod
from typing import Any

from pydantic import ValidationError
from twisted.python import log

from apricot.models import (
    LDAPAttributeAdaptor,
    LDAPGroupOfNames,
    LDAPInetOrgPerson,
    LDAPInetUser,
    LDAPOAuthUser,
    LDAPPerson,
    LDAPPosixAccount,
    LDAPPosixGroup,
)

from .oauth_client import OAuthClient


class OAuthClientAdaptor(OAuthClient):
    """Adaptor for converting raw user and group data into LDAP format."""

    def __init__(self, **kwargs: Any):
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

    def construct_user_primary_groups(self) -> list[dict[str, Any]]:
        """
        Each user needs a self-titled primary group
        """
        # Add one self-titled group for each user
        user_group_dicts = []
        for user_dict in list(self.unvalidated_users()):
            user_dict["memberUid"] = [user_dict["uid"]]
            user_dict["member"] = [f"CN={user_dict['cn']},OU=users,{self.root_dn}"]
            # Group name is taken from 'cn' which should match the username
            user_dict["cn"] = user_dict["uid"]
            user_group_dicts.append(user_dict)
        return user_group_dicts

    def groups(self) -> list[LDAPAttributeAdaptor]:
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
                # Add 'groupOfNames' attributes
                group_of_names = LDAPGroupOfNames(**group_dict)
                attributes.update(group_of_names.model_dump())
                attributes["objectclass"].append("groupOfNames")
                # Add 'posixGroup' attributes
                posix_group = LDAPPosixGroup(**group_dict)
                attributes.update(posix_group.model_dump())
                attributes["objectclass"].append("posixGroup")
                output.append(LDAPAttributeAdaptor(attributes))
            except ValidationError as exc:
                name = group_dict["cn"] if "cn" in group_dict else "unknown"
                log.msg(f"Validation failed for group '{name}'.")
                for error in exc.errors():
                    log.msg(
                        f"... '{error['loc'][0]}': {error['msg']} but '{error['input']}' was provided."
                    )
        return output

    def users(self) -> list[LDAPAttributeAdaptor]:
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
                user_dict["memberOf"].append(
                    f"CN={user_dict['cn']},OU=groups,{self.root_dn}"
                )
                # Add 'inetOrgPerson' attributes
                inetorg_person = LDAPInetOrgPerson(**user_dict)
                attributes.update(inetorg_person.model_dump())
                attributes["objectclass"].append("inetOrgPerson")
                # Add 'inetUser' attributes
                inet_user = LDAPInetUser(**user_dict)
                attributes.update(inet_user.model_dump())
                attributes["objectclass"].append("inetuser")
                # Add 'person' attributes
                person = LDAPPerson(**user_dict)
                attributes.update(person.model_dump())
                attributes["objectclass"].append("person")
                # Add 'posixAccount' attributes
                posix_account = LDAPPosixAccount(**user_dict)
                attributes.update(posix_account.model_dump())
                attributes["objectclass"].append("posixAccount")
                # Add 'OAuthUser' attributes
                oauth_user = LDAPOAuthUser(**user_dict)
                attributes.update(oauth_user.model_dump())
                attributes["objectclass"].append("oauthUser")
                output.append(LDAPAttributeAdaptor(attributes))
            except ValidationError as exc:
                name = user_dict["cn"] if "cn" in user_dict else "unknown"
                log.msg(f"Validation failed for user '{name}'.")
                for error in exc.errors():
                    log.msg(
                        f"... '{error['loc'][0]}': {error['msg']} but '{error['input']}' was provided."
                    )
        return output
