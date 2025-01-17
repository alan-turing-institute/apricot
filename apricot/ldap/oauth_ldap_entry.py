from __future__ import annotations

from typing import Self, cast

from ldaptor.inmemory import ReadOnlyInMemoryLDAPEntry
from ldaptor.protocols.ldap.distinguishedname import (
    DistinguishedName,
    RelativeDistinguishedName,
)
from ldaptor.protocols.ldap.ldaperrors import (
    LDAPEntryAlreadyExists,
    LDAPInvalidCredentials,
)
from twisted.internet import defer
from twisted.logger import Logger

from apricot.oauth import LDAPAttributeDict, OAuthClient


class OAuthLDAPEntry(ReadOnlyInMemoryLDAPEntry):
    """An LDAP entry that represents a view of an OAuth object."""

    dn: DistinguishedName
    attributes: LDAPAttributeDict

    def __init__(
        self: Self,
        dn: DistinguishedName | str,
        attributes: LDAPAttributeDict,
        oauth_client: OAuthClient | None = None,
    ) -> None:
        """Initialise an OAuthLDAPEntry.

        Args:
            dn: Distinguished Name of the object
            attributes: Attributes of the object.
            oauth_client: An OAuth client used for binding
        """
        self.logger = Logger()
        self.oauth_client_ = oauth_client
        if not isinstance(dn, DistinguishedName):
            dn = DistinguishedName(stringValue=dn)
        super().__init__(dn, attributes)

    def __str__(self: Self) -> str:
        """Return a string representation of this entry and its children.

        Returns:
            A multiline string representing this LDAP entry together with an entry for
            each child indented by two additional spaces and an empty line between each
            child.
        """
        # Convert internal representation to list of strings
        lines = [
            line.strip()
            for line in bytes(self.toWire()).decode("utf-8").strip().split("\n")
        ]
        # Add each child with an empty line to separate them
        for child in self.list_children():
            lines += [f"  {line}" for line in str(child).split("\n")] + [""]
        return "\n".join(lines)

    @property
    def oauth_client(self: Self) -> OAuthClient:
        """Find the OAuth client used by this OAuthLDAPEntry.

        If it does not already have one, then use the parent entry.

        Returns:
            The OAuth client used by this OAuthLDAPEntry.

        Raises:
            TypeError: if the OAuth client could not be found.
        """
        if not self.oauth_client_ and hasattr(self._parent, "oauth_client"):
            self.oauth_client_ = self._parent.oauth_client
        if not isinstance(self.oauth_client_, OAuthClient):
            msg = f"OAuthClient is of incorrect type {type(self.oauth_client_)}"
            raise TypeError(msg)
        return self.oauth_client_

    def add_child(
        self: Self,
        rdn: RelativeDistinguishedName | str,
        attributes: LDAPAttributeDict,
    ) -> OAuthLDAPEntry:
        """Attempt to a child to this entry or return one that already exists.

        Args:
            rdn: The relative distinguished name of the child
            attributes: The LDAP attributes of the child

        Returns:
            An OAuthLDAPEntry for the child.
        """
        if isinstance(rdn, str):
            rdn = RelativeDistinguishedName(stringValue=rdn)
        try:
            output = self.addChild(rdn, attributes)
        except LDAPEntryAlreadyExists:
            self.logger.warn(
                "Refusing to add child '{child}' as it already exists.",
                child=rdn.getText(),
            )
            output = self._children[rdn.getText()]
        return cast("OAuthLDAPEntry", output)

    def bind(self: Self, password: bytes) -> defer.Deferred[OAuthLDAPEntry]:
        """Attempt to authenticate as this user.

        Args:
            password: Password for this user

        Returns:
            A deferred OAuthLDAPEntry if the password is correct or a deferred Failure
            if not.
        """

        def _bind(password: bytes) -> OAuthLDAPEntry:
            oauth_username = next(iter(self.get("oauth_username", "unknown")))
            s_password = password.decode("utf-8")
            if self.oauth_client.verify(username=oauth_username, password=s_password):
                return self
            msg = f"Invalid password for user '{oauth_username}'."
            self.logger.error(msg)
            raise LDAPInvalidCredentials(msg)

        return defer.maybeDeferred(_bind, password)

    def list_children(self: Self) -> list[OAuthLDAPEntry]:
        """Return a list of LDAP children.

        Returns:
            A list of child OAuthLDAPEntry.
        """
        return [cast("OAuthLDAPEntry", entry) for entry in self._children.values()]
