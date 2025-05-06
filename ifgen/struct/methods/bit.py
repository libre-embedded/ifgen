"""
A module implementing interfaces for generating bit-field methods.
"""

# built-in
from typing import Any

# third-party
from vcorelib.io.file_writer import IndentedFileWriter

# internal
from ifgen.generation.interface import GenerateTask


def handle_description(
    writer: IndentedFileWriter, field: dict[str, Any]
) -> None:
    """Handle writing an instance's description."""

    if field.get("description"):
        writer.empty()
        writer.write(field["description"])


def set_bit_method(
    task: GenerateTask,
    name: str,
    field: dict[str, Any],
    writer: IndentedFileWriter,
    method_slug: str,
) -> None:
    """Generate a 'set' method for a bit-field."""

    method = task.cpp_namespace(f"set_{method_slug}(){task.method_suffix()}")
    writer.empty()

    with writer.javadoc():
        writer.write(f"Set {name}'s {field['name']} bit.")
        handle_description(writer, field)

    writer.write("inline void " + method)

    with writer.scope():
        stmt = f"1u << {field['index']}u"
        writer.write(f"{name} |= {stmt};")


def clear_bit_method(
    task: GenerateTask,
    name: str,
    field: dict[str, Any],
    writer: IndentedFileWriter,
    method_slug: str,
) -> None:
    """Generate a 'clear' method for a bit-field."""

    method = task.cpp_namespace(f"clear_{method_slug}(){task.method_suffix()}")
    writer.empty()

    with writer.javadoc():
        writer.write(f"Clear {name}'s {field['name']} bit.")
        handle_description(writer, field)

    writer.write("inline void " + method)

    with writer.scope():
        stmt = f"~(1u << {field['index']}u)"
        writer.write(f"{name} &= {stmt};")


def bit_field_toggle_method(
    task: GenerateTask,
    name: str,
    field: dict[str, Any],
    writer: IndentedFileWriter,
    method_slug: str,
) -> None:
    """Generate a 'toggle' method for a bit-field."""

    set_bit_method(task, name, field, writer, method_slug)
    clear_bit_method(task, name, field, writer, method_slug)

    method = task.cpp_namespace(
        f"toggle_{method_slug}(){task.method_suffix()}"
    )
    writer.empty()

    with writer.javadoc():
        writer.write(f"Toggle {name}'s {field['name']} bit.")
        handle_description(writer, field)

    writer.write("inline void " + method)

    with writer.scope():
        stmt = f"1u << {field['index']}u"
        writer.write(f"{name} ^= {stmt};")
