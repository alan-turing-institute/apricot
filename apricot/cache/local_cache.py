from typing import Self

from .uid_cache import UidCache


class LocalCache(UidCache):
    def __init__(self: Self) -> None:
        self.cache: dict[str, int] = {}

    def get(self: Self, identifier: str) -> int | None:
        return self.cache.get(identifier, None)

    def keys(self: Self) -> list[str]:
        return [str(k) for k in self.cache.keys()]

    def set(self: Self, identifier: str, uid_value: int) -> None:
        self.cache[identifier] = uid_value

    def values(self: Self, keys: list[str]) -> list[int]:
        return [v for k, v in self.cache.items() if k in keys]
