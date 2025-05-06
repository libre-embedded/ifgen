"""
A module implementing 'set' methods for bit-fields.
"""

# built-in
from typing import Any, Iterator

# third-party
from vcorelib.io.file_writer import IndentedFileWriter

# internal
from ifgen.generation.interface import GenerateTask
from ifgen.struct.methods.bit import (
    bit_field_toggle_method,
    handle_description,
)
from ifgen.struct.methods.fields.common import (
    BitField,
    bit_field_method_slug,
    bit_field_underlying,
    bit_mask_literal,
    possible_array_arg,
)


def bit_field_set_all_method(
    task: GenerateTask,
    writer: IndentedFileWriter,
    field: dict[str, Any],
    fields: list[BitField],
    alias: str = None,
) -> None:
    """Generate a 'set' method for multiple bit-field."""

    name = field["name"] if not alias else alias

    inner = possible_array_arg(field)
    if inner:
        inner += ", "

    with writer.javadoc():
        writer.write(f"Set all of {name}'s bit fields.")
        handle_description(writer, field)

    # Add field args.
    args = []
    for bit_field in fields:
        args.append(f"{bit_field_underlying(bit_field)} {bit_field['name']}")

    inner += ", ".join(args)
    writer.write(f"inline void set_{name}({inner}){task.method_suffix()}")
    with writer.scope():
        rhs = field["name"] if not alias else alias
        if "index" in inner:
            rhs += "[index]"

        writer.write(f"{field['type']} curr = {rhs};")

        with writer.padding():
            for bit_field in fields:
                for line in bit_field_set_lines(
                    task, bit_field, value=bit_field["name"]
                ):
                    writer.write(line)

        writer.write(f"{rhs} = curr;")


def bit_field_set_lines(
    task: GenerateTask,
    field: BitField,
    lhs: str = "curr",
    value: str = "value",
) -> Iterator[str]:
    """Get lines that perform a bit-field's assignment."""

    mask = bit_mask_literal(field["width"])

    yield f"{lhs} &= ~({mask} << {field['index']}u);"

    val_str = value
    if task.env.is_enum(bit_field_underlying(field)):
        val_str = f"std::to_underlying({val_str})"

    yield f"{lhs} |= ({val_str} & {mask}) << {field['index']}u;"


def bit_field_set_method(
    task: GenerateTask,
    parent: dict[str, Any],
    field: BitField,
    writer: IndentedFileWriter,
    alias: str = None,
) -> None:
    """Generate a 'set' method for a bit-field."""

    method_slug = bit_field_method_slug(parent, field["name"], alias=alias)
    kind = bit_field_underlying(field)

    # Generate a toggle method for bit fields.
    if field["width"] == 1:
        bit_field_toggle_method(
            task, parent["name"], field, writer, method_slug
        )
    else:
        inner = possible_array_arg(parent)
        if inner:
            inner += ", "
        inner += f"{kind} value"

        method = task.cpp_namespace(
            f"set_{method_slug}({inner}){task.method_suffix()}"
        )
        writer.empty()

        with writer.javadoc():
            writer.write(f"Set {parent['name']}'s {field['name']} field.")
            handle_description(writer, field)

        writer.write("inline void " + method)
        with writer.scope():
            rhs = parent["name"] if not alias else alias
            if "index" in inner:
                rhs += "[index]"

            writer.write(f"{parent['type']} curr = {rhs};")

            with writer.padding():
                for line in bit_field_set_lines(task, field):
                    writer.write(line)

            writer.write(f"{rhs} = curr;")
