"""
A module for generating struct source files.
"""

# internal
from ifgen.generation.interface import GenerateTask
from ifgen.struct.methods import struct_methods
from ifgen.struct.methods.fields import bit_fields
from ifgen.struct.stream import struct_stream_methods


def create_struct_source(task: GenerateTask) -> None:
    """Create a header file based on a struct definition."""

    if task.is_python:
        return

    if task.instance["stream"] or task.instance["codec"]:
        with task.source_boilerplate([]) as writer:
            struct_methods(task, writer, False)
            bit_fields(task, writer, False)
            if task.instance["stream"]:
                writer.empty()
                struct_stream_methods(task, writer, False)
