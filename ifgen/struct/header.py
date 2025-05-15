"""
A module implementing a struct header-file interface generator.
"""

# built-in
from contextlib import ExitStack
from typing import Any

# third-party
from vcorelib.io.file_writer import (
    CommentStyle,
    IndentedFileWriter,
    LineWithComment,
)

# internal
from ifgen.generation.interface import GenerateTask
from ifgen.struct.methods import struct_methods
from ifgen.struct.methods.fields import bit_fields
from ifgen.struct.python import python_struct_header
from ifgen.struct.stream import struct_stream_methods

FieldConfig = dict[str, int | str]


def enforce_expected_size(
    size: int, data: dict[str, Any], assert_msg: str
) -> None:
    """Enforce an expected-size field."""

    # If expected size is set, verify it.
    if "expected_size" in data:
        assert data["expected_size"] == size, (
            assert_msg,
            data["expected_size"],
            size,
        )


def struct_line(
    name: str,
    value: FieldConfig,
    volatile: bool,
    const: bool,
    array_length: int = None,
    default: str = None,
) -> LineWithComment:
    """Build a string for a struct-field line."""

    line = f"{value['type']} {name}"
    if array_length is not None:
        line += f"[{name}_length]"

    prefix = "volatile " if volatile else ""
    prefix += "const " if const else ""

    if default:
        line += f" = {default}"
    elif const:
        line += " = {}"

    return prefix + f"{line};", value.get("description")  # type: ignore


def struct_fields(task: GenerateTask, writer: IndentedFileWriter) -> None:
    """Generate struct fields."""

    writer.c_comment("Fields.")

    with writer.trailing_comment_lines(style=CommentStyle.C_DOXYGEN) as lines:
        # Fields.
        for field in task.instance["fields"]:
            enforce_expected_size(
                task.env.size(field["type"]) * field.get("array_length", 1),
                field,
                f"{task.name}.{field['name']}",
            )

            if "array_length" in field:
                lines.append(
                    (
                        (
                            f"static constexpr std::size_t "
                            f"{field['name']}_length = "
                            f"{field['array_length']};"
                        ),
                        None,
                    )
                )

            with ExitStack() as stack:
                is_union = field.get("alternates")
                all_fields = [field]
                if is_union:
                    writer.write("union")
                    stack.enter_context(writer.scope(suffix=";"))
                    all_fields.extend(field["alternates"])

                for possible_union in all_fields:
                    if "type" not in possible_union:
                        possible_union["type"] = field["type"]

                    # Handle enum defaults.
                    default = None
                    if task.env.is_enum(possible_union["type"]):
                        enum = task.env.get_enum(possible_union["type"])
                        if enum.default:
                            default = f"{possible_union['type']}_default"
                            if "array_length" in field:
                                default = (
                                    "{"
                                    + ", ".join(
                                        [
                                            default
                                            for _ in range(
                                                field["array_length"]
                                            )
                                        ]
                                    )
                                    + "}"
                                )

                    line, comment = struct_line(
                        possible_union["name"],
                        possible_union,
                        possible_union["volatile"],
                        possible_union["const"],
                        array_length=possible_union.get("array_length"),
                        default=default,
                    )
                    if is_union:
                        writer.write(
                            line + ("" if not comment else f" /* {comment} */")
                        )
                    else:
                        lines.append((line, comment))

        lines.append(("", None))


def struct_instance(
    task: GenerateTask, writer: IndentedFileWriter, instance: dict[str, Any]
) -> None:
    """Generate struct instances."""

    writer.empty()

    if instance.get("description"):
        with writer.javadoc():
            writer.write(instance["description"])

    type_base = f"{task.name} *"
    writer.write(
        (
            "static "
            + ("volatile " if instance["volatile"] else "")
            + f"{type_base}const "
            f"{instance['name']} = "
            f"reinterpret_cast<{type_base}>({instance['address']});"
        )
    )


def cpp_struct_header(task: GenerateTask, writer: IndentedFileWriter) -> None:
    """Create the contents of a C++ struct header file."""

    attributes = ["gnu::packed"]
    writer.write(f"struct [[{', '.join(attributes)}]] {task.name}")
    with writer.scope(suffix=";"):
        writer.c_comment("Constant attributes.")
        with writer.trailing_comment_lines(
            style=CommentStyle.C_DOXYGEN
        ) as lines:
            if task.instance["identifier"]:
                lines.append(
                    (
                        "static constexpr struct_id_t "
                        f"id = {task.protocol().id};",
                        f"{task.name}'s identifier.",
                    )
                )

            # trace=True
            size = task.env.size(task.name)
            enforce_expected_size(size, task.instance, task.name)

            lines.append(
                (
                    f"static constexpr std::size_t size = {size};",
                    f"{task.name}'s size in bytes.",
                )
            )

        writer.empty()
        struct_fields(task, writer)

        # Methods.
        writer.c_comment("Methods.")

        if task.instance["methods"]:
            struct_methods(task, writer)

        bit_fields(task, writer)

    # Add size assertion.
    writer.empty()
    writer.write(f"static_assert(sizeof({task.name}) == {task.name}::size);")
    writer.write(f"static_assert(ifgen_struct<{task.name}>);")

    if task.instance["stream"]:
        writer.empty()
        struct_stream_methods(task, writer)

    for instance in task.instance.get("instances", []):
        struct_instance(task, writer, instance)


def struct_header(task: GenerateTask, writer: IndentedFileWriter) -> None:
    """Create the contents of a struct header file."""

    if task.is_cpp:
        cpp_struct_header(task, writer)
    elif task.is_python:
        python_struct_header(task, writer)
