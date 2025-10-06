"""
A module for handling SVD bit-field enumerations.
"""

# built-in
from os.path import commonprefix
from typing import Any

# internal
from ifgen.svd.model.enum import EnumeratedValues

EnumValues = dict[str, Any]
ENUM_DEFAULTS: dict[str, Any] = {
    "unit_test": False,
    "json": False,
    "use_map": False,
    "identifier": False,
}

BY_HASH: dict[str, dict[int, str]] = {}
PRUNE_ENUMS = False


def get_enum_name(name: str, peripheral: str, raw_mapping: EnumValues) -> str:
    """Get the name of an enumeration."""

    if not PRUNE_ENUMS:
        return name

    hashed = hash(
        ",".join(
            name + f"={val['value']}"
            for name, val in sorted(raw_mapping.items())
        )
    )

    BY_HASH.setdefault(peripheral, {})

    for_periph = BY_HASH[peripheral]
    for_periph.setdefault(hashed, name)

    return for_periph[hashed]


IGNORE_WORDS = {
    "the",
    "as",
    "a",
    "is",
    "will",
    "but",
    "are",
    "yet",
    "that",
    "to",
    "and",
    "in",
    "of",
    "on",
    "for",
    "from",
    "its",
    "it",
}


def is_name_part(value: str) -> bool:
    """Determine if a word should be part of an enumeration value name."""
    return bool(value) and value not in IGNORE_WORDS


def as_alnum(word: str) -> str:
    """Get a word's alpha-numeric contents only."""

    result = ""
    for char in word:
        if char.isalnum() or char == "_":
            result += char

    return result


SKIP = {"-"}


def handle_enum_name(name: str, description: str = None) -> str:
    """Attempt to generate more useful enumeration names."""

    if name.startswith("value") and description:
        alnum_parts = [
            as_alnum(x.strip().lower().replace("-", "_"))
            for x in description.split()
            if x not in SKIP
        ]

        # Prune some words if the description is very long.
        if len(alnum_parts) > 1:
            alnum_parts = list(filter(is_name_part, alnum_parts))

        assert alnum_parts, (name, description)

        new_name = "_".join(alnum_parts)

        assert new_name, (name, description)
        name = new_name

    return name


def remove_common_prefixes(data: dict[str, Any]) -> dict[str, Any]:
    """Attempt to remove common prefixes in enumeration names."""

    result = data

    length = len(commonprefix(list(result)))
    if length > 1:
        result = {
            key[length:] if length < len(key) else key: value
            for key, value in result.items()
        }

    return result


def handle_duplicate(existing: dict[str, Any], key: str, value: Any) -> None:
    """Handle key de-duplication for enumerations."""

    assert key
    if key[0].isnumeric():
        key = "_" + key

    while key in existing:
        key += "_x"

    existing[key] = value


def translate_enums(enum: EnumeratedValues) -> EnumValues:
    """Generate an enumeration definition."""

    result: dict[str, Any] = {}
    enum.handle_description(result)

    for name, value in enum.derived_elem.enum.items():
        enum_data: dict[str, Any] = {}
        value.handle_description(enum_data)

        value_str: str = value.raw_data["value"].lower()

        prefix = ""
        for possible_prefix in ("#", "0b", "0x"):
            if value_str.startswith(possible_prefix):
                prefix = possible_prefix
                break

        if prefix in ("#", "0b"):
            enum_data["value"] = int(
                value_str[len(prefix) :].replace("x", "1"), 2
            )
        elif prefix == "0x":
            enum_data["value"] = int(value_str[len(prefix) :], 16)
        else:
            enum_data["value"] = int(value_str)

        handle_duplicate(
            result,
            handle_enum_name(name, value.raw_data.get("description")),
            enum_data,
        )

    # Truncate names.
    new_result: dict[str, Any] = {}
    for key, value in remove_common_prefixes(result).items():
        handle_duplicate(
            new_result, key if len(key) < 51 else key[:45] + "_cont", value
        )

    return new_result
