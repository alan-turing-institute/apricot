from typing import Any

JSONDict = dict[str, Any]
JSONKey = list[Any] | dict[str, Any] | Any
LDAPAttributeDict = dict[str, list[str]]
LDAPControlTuple = tuple[str, bool, Any]
