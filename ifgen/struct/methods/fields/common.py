"""
Common utilities for generating bit-field related struct methods.
"""

# built-in
from typing import Any, Optional

BitField = dict[str, Any]


def bit_mask_literal(width: int) -> str:
    """Get a bit-mask literal."""

    if width % 4 == 0:
        return "0x" + ("f" * (width // 4)) + "u"
    return "0b" + ("1" * width) + "u"


def possible_array_arg(parent: dict[str, Any]) -> str:
    """Determine if a method needs an array-index argument."""

    array_length: Optional[int] = parent.get("array_length")
    inner = ""
    if array_length:
        inner = "std::size_t index"

    return inner


STANDARD_INTS = [
    ("uint8_t", 8),
    ("uint16_t", 16),
    ("uint32_t", 32),
    ("uint64_t", 64),
]


def bit_field_underlying(field: dict[str, Any]) -> str:
    """Get the underlying type for a bit field."""

    kind = field.get("type")

    # Automatically determine a sane primitive-integer type to use if one isn't
    # specified.
    if kind is None:
        width = field["width"]

        if width == 1:
            kind = "bool"
        else:
            for candidate, bit_width in STANDARD_INTS:
                if field["width"] <= bit_width:
                    kind = candidate
                    break

    assert kind is not None, kind
    return kind


def bit_field_method_slug(
    field: dict[str, Any], member: str = "", alias: str = None
) -> str:
    """Get a method slug for a struct's bit-field method."""

    name = str(field["name"]) if not alias else alias
    if member and member != name:
        name += "_" + member
    return name
