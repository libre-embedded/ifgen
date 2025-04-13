"""
A module for generating enumeration source files.
"""

# third-party
from vcorelib.io import IndentedFileWriter

# internal
from ifgen.enum.common import enum_to_string_function, string_to_enum_function
from ifgen.generation.interface import GenerateTask


def enum_source(task: GenerateTask, writer: IndentedFileWriter) -> None:
    """Create a source file for an enumeration."""

    enum_to_string_function(task, writer, task.instance["use_map"])
    writer.empty()
    string_to_enum_function(task, writer, task.instance["use_map"])


def create_enum_source(task: GenerateTask) -> None:
    """Create a source file based on an enum definition."""

    if task.is_python:
        return

    if task.instance["use_map"]:
        with task.source_boilerplate(["<map>", "<string>"]) as writer:
            enum_source(task, writer)
