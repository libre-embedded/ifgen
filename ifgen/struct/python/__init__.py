"""
A module implementing Python struct-generation interfaces.
"""

# third-party
from vcorelib.io import IndentedFileWriter

# internal
from ifgen.generation.interface import GenerateTask


def python_struct_header(
    task: GenerateTask, writer: IndentedFileWriter
) -> None:
    """Create a Python module for a struct."""

    writer.empty()

    del task
    writer.write("# todo")
