from typing import Any

JSONDict = dict[str, str | list[str]]
LDAPAttributeDict = dict[str, list[str]]
LDAPControlTuple = tuple[str, bool, Any]
