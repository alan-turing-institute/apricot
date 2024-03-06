from typing import Any

JSONDict = dict[str, str | list[str]]
LDAPAttributeDict = dict[str, list[Any]]
LDAPControlTuple = tuple[str, bool, Any]
