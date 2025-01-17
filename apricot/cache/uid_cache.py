from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Self, cast


class UidCache(ABC):
    """Abstract cache for storing UIDs."""

    @abstractmethod
    def get(self: Self, identifier: str) -> int | None:
        """Get the UID for a given identifier, returning None if it does not exist.

        Args:
            identifier: identifier key to set

        Returns:
            Value for this identifier or None if it does not exist.
        """

    @abstractmethod
    def keys(self: Self) -> list[str]:
        """Get list of cached keys.

        Returns:
            A list of keys to entries in the cache.
        """

    @abstractmethod
    def set(self: Self, identifier: str, uid_value: int) -> None:
        """Set the UID for a given identifier.

        Args:
            identifier: identifier key to set
            uid_value: value to set for this identifier
        """

    @abstractmethod
    def values(self: Self, keys: list[str]) -> list[int]:
        """Get list of cached values corresponding to requested keys.

        Args:
            keys: list of keys to lookup

        Returns:
            A value for each key
        """

    def get_group_uid(self: Self, identifier: str) -> int:
        """Get UID for a group, constructing one if necessary.

        Args:
            identifier: Identifier for group needing a UID

        Returns:
            The UID for this group.
        """
        return self.get_uid(identifier, category="group", min_value=3000)

    def get_user_uid(self: Self, identifier: str) -> int:
        """Get UID for a user, constructing one if necessary.

        Args:
            identifier: Identifier for user needing a UID

        Returns:
            The UID for this user.
        """
        return self.get_uid(identifier, category="user", min_value=2000)

    def get_uid(
        self: Self,
        identifier: str,
        category: str,
        min_value: int | None = None,
    ) -> int:
        """Get UID, constructing one if necessary.

        Args:
            identifier: Identifier for object needing a UID
            category: Category the object belongs to
            min_value: Minimum allowed value for the UID

        Returns:
            The UID for a given identifier.
        """
        identifier_ = f"{category}-{identifier}"
        uid = self.get(identifier_)
        if not uid:
            min_value = min_value or 0
            next_uid = max(self._get_max_uid(category) + 1, min_value)
            self.set(identifier_, next_uid)
        return cast("int", self.get(identifier_))

    def _get_max_uid(self: Self, category: str | None) -> int:
        """Get maximum UID for a given category.

        Args:
            category: Category to check UIDs for

        Returns:
            The maximum UID for this category
        """
        if category:
            keys = [k for k in self.keys() if k.startswith(category)]
        else:
            keys = self.keys()
        values = [*self.values(keys), -999]
        return max(values)

    def overwrite_group_uid(self: Self, identifier: str, uid: int) -> None:
        """Set UID for a group, overwriting the existing value if there is one.

        Args:
            identifier: Identifier for group
            uid: Desired UID
        """
        return self.overwrite_uid(identifier, category="group", uid=uid)

    def overwrite_user_uid(self: Self, identifier: str, uid: int) -> None:
        """Get UID for a user, constructing one if necessary.

        Args:
            identifier: Identifier for user
            uid: Desired UID
        """
        return self.overwrite_uid(identifier, category="user", uid=uid)

    def overwrite_uid(self: Self, identifier: str, category: str, uid: int) -> None:
        """Set UID, overwriting the existing one if necessary.

        Args:
            identifier: Identifier for object
            category: Category the object belongs to
            uid: Desired UID
        """
        self.set(f"{category}-{identifier}", uid)
