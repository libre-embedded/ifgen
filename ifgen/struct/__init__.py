"""
A module implementing interfaces for struct-file generation.
"""

# built-in
from typing import Dict, Iterable, Union

# internal
from ifgen import PKG_NAME
from ifgen.generation.interface import GenerateTask
from ifgen.struct.header import struct_header
from ifgen.struct.source import create_struct_source
from ifgen.struct.test import create_struct_test

__all__ = ["create_struct", "create_struct_test", "create_struct_source"]
FieldConfig = Dict[str, Union[int, str]]


def header_for_type(name: str, task: GenerateTask) -> str:
    """Determine the header file to import for a given type."""

    candidate = task.custom_include(name)
    if candidate:
        return f'"{candidate}"'

    return ""


def struct_dependencies(task: GenerateTask) -> set[str]:
    """Generates string type names for dependencies."""

    unique = set()

    for config in task.instance["fields"]:
        if "type" in config:
            unique.add(config["type"])

        # Add includes for bit-fields.
        for bit_field in config.get("fields", []):
            if "type" in bit_field:
                unique.add(bit_field["type"])

        # Add includes for alternates.
        for alternate in config.get("alternates", []):
            for alternate_bit_field in alternate.get("fields", []):
                if "type" in alternate_bit_field:
                    unique.add(alternate_bit_field["type"])

    return unique


def struct_includes(task: GenerateTask) -> Iterable[str]:
    """Determine headers that need to be included for a given struct."""

    result = [header_for_type(x, task) for x in struct_dependencies(task)]
    result.append(f'"../{PKG_NAME}/common.h"')
    return result


def create_struct(task: GenerateTask) -> None:
    """Create a header file based on a struct definition."""

    with task.boilerplate(
        includes=struct_includes(task),
        json=task.instance.get("json", False),
        parent_depth=2,
    ) as writer:
        struct_header(task, writer)
