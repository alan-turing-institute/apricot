from .uid_cache import UidCache


class LocalCache(UidCache):
    def __init__(self) -> None:
        self.cache: dict[str, int] = {}

    def get(self, identifier: str) -> int | None:
        return self.cache.get(identifier, None)

    def keys(self) -> list[str]:
        return [str(k) for k in self.cache.keys()]

    def set(self, identifier: str, uid_value: int) -> None:
        self.cache[identifier] = uid_value

    def values(self, keys: list[str]) -> list[int]:
        return [v for k, v in self.cache.items() if k in keys]
