"""
A module for working with schemas belonging to this package.
"""

# built-in
from typing import Any
from typing import Optional as _Optional

# third-party
from vcorelib.dict.codec import DictCodec as _DictCodec
from vcorelib.io import DEFAULT_INCLUDES_KEY
from vcorelib.schemas.base import SchemaMap as _SchemaMap
from vcorelib.schemas.json import JsonSchemaMap as _JsonSchemaMap

# internal
from ifgen import PKG_NAME


class IfgenDictCodec(_DictCodec):
    """
    A simple wrapper for package classes that want to implement DictCodec.
    """

    data: dict[str, Any]

    default_schemas: _Optional[_SchemaMap] = _JsonSchemaMap.from_package(
        PKG_NAME,
        includes_key=DEFAULT_INCLUDES_KEY,
    )
