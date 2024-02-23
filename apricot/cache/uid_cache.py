from typing import cast

import redis


class UidCache:
    def __init__(self, redis_host: str, redis_port: str) -> None:
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.cache_ = None

    @property
    def cache(self) -> redis.Redis:  # type: ignore[type-arg]
        """
        Lazy-load the cache on request
        """
        if not self.cache_:
            self.cache_ = redis.Redis(  # type: ignore[call-overload]
                host=self.redis_host, port=self.redis_port, decode_responses=True
            )
        return self.cache_  # type: ignore[return-value]

    @property
    def keys(self) -> list[str]:
        """
        Get list of keys from the cache
        """
        return [str(k) for k in self.cache.keys()]

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
        uid = self.cache.get(identifier_)
        if not uid:
            min_value = min_value if min_value else 0
            next_uid = max(self._get_max_uid(category) + 1, min_value)
            self.cache.set(identifier_, next_uid)
        return cast(int, self.cache.get(identifier_))

    def _get_max_uid(self, category: str | None) -> int:
        """
        Get maximum UID for a given category

        @param category: Category to check UIDs for
        """
        if category:
            keys = [k for k in self.keys if k.startswith(category)]
        else:
            keys = self.keys
        values = [int(cast(str, v)) for v in self.cache.mget(keys)] + [-999]
        return max(values)
