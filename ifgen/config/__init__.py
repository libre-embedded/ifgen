"""
A module implementing a configuration interface for the package.
"""

# built-in
from typing import Any

# third-party
from vcorelib.dict import merge
from vcorelib.dict.codec import BasicDictCodec as _BasicDictCodec
from vcorelib.io import ARBITER as _ARBITER
from vcorelib.io import DEFAULT_INCLUDES_KEY
from vcorelib.io.types import JsonObject as _JsonObject
from vcorelib.paths import Pathlike, find_file

# internal
from ifgen import PKG_NAME
from ifgen.schemas import IfgenDictCodec


class Config(IfgenDictCodec, _BasicDictCodec):
    """The top-level configuration object for the package."""

    def init(self, data: _JsonObject) -> None:
        """Initialize this instance."""

        super().init(data)

        common = ["identifier", "unit_test"]

        # Forward enum settings.
        enum_forwards = common + ["use_map"]
        enum: dict[str, Any]
        for enum in data.get("enums", {}).values():  # type: ignore
            for forward in enum_forwards:
                enum.setdefault(
                    forward,
                    data["enum"][forward],  # type: ignore
                )

        # Forward struct settings.
        struct_forwards = common + [
            "codec",
            "stream",
            "methods",
            "default_endianness",
        ]
        struct: dict[str, Any]
        for struct in data.get("structs", {}).values():  # type: ignore
            for forward in struct_forwards:
                struct.setdefault(
                    forward,
                    data["struct"][forward],  # type: ignore
                )


def load(path: Pathlike) -> Config:
    """Load a configuration object."""

    src_config = find_file("default.yaml", package=PKG_NAME)
    assert src_config is not None

    data = merge(
        _ARBITER.decode(
            src_config,
            includes_key=DEFAULT_INCLUDES_KEY,
            require_success=True,
        ).data,
        _ARBITER.decode(
            path, includes_key=DEFAULT_INCLUDES_KEY, require_success=True
        ).data,
        # Always allow the project-specific configuration to override package
        # data.
        expect_overwrite=True,
    )

    return Config.create(data)
