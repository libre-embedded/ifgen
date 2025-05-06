"""
A module implementing 'get' methods for bit-fields.
"""

# built-in
from typing import Any

# third-party
from vcorelib.io.file_writer import IndentedFileWriter

# internal
from ifgen.generation.interface import GenerateTask
from ifgen.struct.methods.bit import handle_description
from ifgen.struct.methods.fields.common import (
    BitField,
    bit_field_method_slug,
    bit_field_underlying,
    bit_mask_literal,
    possible_array_arg,
)


def bit_field_get_all_method(
    task: GenerateTask,
    writer: IndentedFileWriter,
    field: dict[str, Any],
    fields: list[BitField],
    alias: str = None,
) -> None:
    """Generate a 'get' method for multiple bit-field."""

    name = field["name"] if not alias else alias

    inner = possible_array_arg(field)
    if inner:
        inner += ", "

    with writer.javadoc():
        writer.write(f"Get all of {name}'s bit fields.")
        handle_description(writer, field)

    # Add field args.
    args = []
    for bit_field in fields:
        args.append(f"{bit_field_underlying(bit_field)} &{bit_field['name']}")

    inner += ", ".join(args)

    writer.write(f"inline void get_{name}({inner}){task.method_suffix()}")
    with writer.scope():
        rhs = field["name"] if not alias else alias
        if "index" in inner:
            rhs += "[index]"

        writer.write(f"{field['type']} curr = {rhs};")
        writer.empty()

        for bit_field in fields:
            stmt = get_bit_field_statement(task, bit_field, "curr")
            writer.write(f"{bit_field['name']} = {stmt};")


def get_bit_field_statement(
    task: GenerateTask, field: BitField, lhs: str
) -> str:
    """
    Get the arithmetic statement associated with a bit-field get operation.
    """

    kind = bit_field_underlying(field)

    is_flag = field["width"] == 1

    if is_flag:
        stmt = f"{lhs} & (1u << {field['index']}u)"
    else:
        stmt = (
            f"({lhs} >> {field['index']}u) & "
            f"{bit_mask_literal(field['width'])}"
        )

    if task.env.is_enum(kind):
        stmt = f"{kind}({stmt})"

    return stmt


def bit_field_get_method(
    task: GenerateTask,
    parent: dict[str, Any],
    field: BitField,
    writer: IndentedFileWriter,
    alias: str = None,
) -> None:
    """Generate a 'get' method for a bit-field."""

    inner = possible_array_arg(parent)

    method_slug = bit_field_method_slug(parent, field["name"], alias=alias)
    method = task.cpp_namespace(
        f"get_{method_slug}({inner}){task.method_suffix()}"
    )
    writer.empty()

    with writer.javadoc():
        writer.write(
            (
                f"Get {parent['name']}'s {field['name']} "
                f"{'field' if field['width'] > 1 else 'bit'}."
            )
        )
        handle_description(writer, field)

    line = f"inline {bit_field_underlying(field)} " + method

    lhs = parent["name"] if not alias else alias
    if inner:
        lhs += "[index]"

    writer.write(line)
    with writer.scope():
        writer.write(f"return {get_bit_field_statement(task, field, lhs)};")
