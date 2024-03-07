from typing import Any

from apricot.types import LDAPAttributeDict


class LDAPAttributeAdaptor:
    def __init__(self, attributes: dict[Any, Any]) -> None:
        self.attributes = {
            str(k): list(map(str, v)) if isinstance(v, list) else [str(v)]
            for k, v in attributes.items()
        }

    def to_dict(self) -> LDAPAttributeDict:
        return self.attributes
