from __future__ import annotations

from typing import Self, overload

from .uid_cache import UidCache


class LocalCache(UidCache):
    """Implementation of UidCache using an in-memory dictionary."""

    def __init__(self: Self) -> None:
        """Initialise a RedisCache."""
        self.cache: dict[str, int] = {}

    @overload  # type: ignore[misc]
    def get(self: Self, identifier: str) -> int | None:
        return self.cache.get(identifier, None)

    @overload  # type: ignore[misc]
    def keys(self: Self) -> list[str]:
        return [str(k) for k in self.cache]

    @overload  # type: ignore[misc]
    def set(self: Self, identifier: str, uid_value: int) -> None:
        self.cache[identifier] = uid_value

    @overload  # type: ignore[misc]
    def values(self: Self, keys: list[str]) -> list[int]:
        return [v for k, v in self.cache.items() if k in keys]
