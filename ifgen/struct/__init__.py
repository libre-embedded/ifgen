"""
A module implementing interfaces for struct-file generation.
"""

# built-in
from typing import Any, Dict, Iterable, Union

# internal
from ifgen import PKG_NAME
from ifgen.generation.interface import GenerateTask
from ifgen.struct.header import struct_header
from ifgen.struct.source import create_struct_source
from ifgen.struct.test import create_struct_test
from ifgen.struct.util import struct_dependencies

__all__ = ["create_struct", "create_struct_test", "create_struct_source"]
FieldConfig = Dict[str, Union[int, str]]


def header_for_type(name: str, task: GenerateTask) -> str:
    """Determine the header file to import for a given type."""

    candidate = task.custom_include(name)
    if candidate:
        return f'"{candidate}"'

    return ""


FLOAT = {"float": "std::float32_t", "double": "std::float64_t"}
VALID = {"std::float32_t", "std::float64_t"}


def handle_struct_field_type(data: dict[str, Any]) -> bool:
    """Handle struct-field floating-point types."""

    if data["type"] in FLOAT:
        data["type"] = FLOAT[data["type"]]

    return data["type"] in VALID


def struct_includes(task: GenerateTask) -> Iterable[str]:
    """Determine headers that need to be included for a given struct."""

    result = [header_for_type(x, task) for x in struct_dependencies(task)]

    include_float = False
    for field in task.instance["fields"]:
        if handle_struct_field_type(field):
            include_float = True

    if include_float:
        result.append("<stdfloat>")

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
