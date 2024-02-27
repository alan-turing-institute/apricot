from abc import ABC, abstractmethod
from typing import cast


class UidCache(ABC):
    @abstractmethod
    def get(self, identifier: str) -> int | None:
        """
        Get the UID for a given identifier, returning None if it does not exist
        """
        pass

    @abstractmethod
    def keys(self) -> list[str]:
        """
        Get list of cached keys
        """
        pass

    @abstractmethod
    def set(self, identifier: str, uid_value: int) -> None:
        """
        Set the UID for a given identifier
        """
        pass

    @abstractmethod
    def values(self, keys: list[str]) -> list[int]:
        """
        Get list of cached values corresponding to requested keys
        """
        pass

    def get_group_uid(self, identifier: str) -> int:
        """
        Get UID for a group, constructing one if necessary

        @param identifier: Identifier for group needing a UID
        """
        return self.get_uid(identifier, category="group", min_value=3000)

    def get_user_uid(self, identifier: str) -> int:
        """
        Get UID for a user, constructing one if necessary

        @param identifier: Identifier for user needing a UID
        """
        return self.get_uid(identifier, category="user", min_value=2000)

    def get_uid(
        self, identifier: str, category: str, min_value: int | None = None
    ) -> int:
        """
        Get UID, constructing one if necessary.

        @param identifier: Identifier for object needing a UID
        @param category: Category the object belongs to
        @param min_value: Minimum allowed value for the UID
        """
        identifier_ = f"{category}-{identifier}"
        uid = self.get(identifier_)
        if not uid:
            min_value = min_value if min_value else 0
            next_uid = max(self._get_max_uid(category) + 1, min_value)
            self.set(identifier_, next_uid)
        return cast(int, self.get(identifier_))

    def _get_max_uid(self, category: str | None) -> int:
        """
        Get maximum UID for a given category

        @param category: Category to check UIDs for
        """
        if category:
            keys = [k for k in self.keys() if k.startswith(category)]
        else:
            keys = self.keys()
        values = [*self.values(keys), -999]
        return max(values)
