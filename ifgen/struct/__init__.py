"""
A module implementing interfaces for struct-file generation.
"""

# built-in
from typing import Iterable

# internal
from ifgen import PKG_NAME
from ifgen.generation.interface import GenerateTask
from ifgen.struct.header import struct_header
from ifgen.struct.test import create_struct_test
from ifgen.struct.util import struct_dependencies

__all__ = ["create_struct", "create_struct_test"]
FieldConfig = dict[str, int | str]


def header_for_type(name: str, task: GenerateTask) -> str:
    """Determine the header file to import for a given type."""

    candidate = task.custom_include(name)
    if candidate:
        return f'"{candidate}"'

    return ""


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
