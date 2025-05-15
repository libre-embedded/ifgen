"""
Utilities shared between struct methods.
"""

# built-in
from contextlib import ExitStack

# third-party
from vcorelib.io import IndentedFileWriter

# internal
from ifgen.generation.interface import GenerateTask


def swap_fields(
    task: GenerateTask, writer: IndentedFileWriter, elem_prefix: str = ""
) -> None:
    """Generate code for swapping struct fields."""

    for field in task.instance["fields"]:
        kind = field["type"]

        if field["padding"] or task.env.size(kind) == 1:
            continue

        name = field["name"]

        with ExitStack() as stack:
            is_array = "array_length" in field
            if is_array:
                array_cmp = task.cpp_namespace(f"{name}_length")
                writer.write(f"for (std::size_t i = 0; i < {array_cmp}; i++)")
                stack.enter_context(writer.scope())

            elem = elem_prefix + name
            if is_array:
                elem += "[i]"

            if task.env.is_struct(kind):
                writer.write(f"{elem}.endian<endianness>();")
            elif task.env.is_enum(kind):
                writer.write(f"{elem} = handle_endian<endianness>({elem});")
            else:
                writer.write(f"{elem} = handle_endian<endianness>({elem});")
