"""
A module implementing interfaces for processing a group of peripherals.
"""

# built-in
from pathlib import Path
from typing import Any

# third-party
from vcorelib.io import ARBITER

# internal
from ifgen.svd.group.base import PeripheralGroup, peripheral_groups
from ifgen.svd.group.fields import EnumMap, StructMap, struct_fields
from ifgen.svd.model.peripheral import Peripheral

__all__ = ["PeripheralGroup", "peripheral_groups", "handle_group"]


def struct_instance(peripheral: Peripheral) -> dict[str, Any]:
    """Get struct instance data."""

    return {
        "name": peripheral.name,
        "address": peripheral.raw_data["baseAddress"],
    }


def struct_data(
    group: PeripheralGroup,
    structs: StructMap,
    enums: EnumMap,
    min_enum_members: int,
) -> dict[str, Any]:
    """Get struct data for a peripheral group."""

    data: dict[str, Any] = {}
    peripheral = group.root
    peripheral.handle_description(data)

    data["instances"] = [struct_instance(x) for x in group.peripherals]
    size, data["fields"] = struct_fields(
        peripheral.registers,
        structs,
        enums,
        peripheral.base_name(lower=False),
        min_enum_members,
    )

    # Too difficult due to padding.
    # data["expected_size"] = size
    del size

    return data


def handle_group(
    output_dir: Path,
    group: PeripheralGroup,
    includes: set[Path],
    min_enum_members: int,
) -> None:
    """Handle a peripheral group."""

    output = output_dir.joinpath("include.yaml")
    includes.add(output)

    structs: StructMap = {}
    enums: EnumMap = {}
    structs[group.root.base_name()] = struct_data(
        group, structs, enums, min_enum_members
    )
    ARBITER.encode(output, {"structs": structs, "enums": enums})
