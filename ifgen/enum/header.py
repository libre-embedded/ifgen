"""
A module for generating enumeration header files.
"""

# built-in
from typing import Optional

# third-party
from vcorelib.io import IndentedFileWriter

# internal
from ifgen.enum.common import enum_to_string_function, string_to_enum_function
from ifgen.enum.python import python_enum_header
from ifgen.generation.interface import GenerateTask
from ifgen.generation.json import to_json_method

EnumConfig = Optional[dict[str, int | str]]


def enum_line(name: str, value: EnumConfig) -> str:
    """Build a string representing a line in an enumeration."""

    line = name

    if value and value.get("value"):
        line += f" = {value['value']}"

    if value and value.get("description"):
        line += f" /*!< {value['description']} */"

    return line


def cpp_enum_neader(task: GenerateTask, writer: IndentedFileWriter) -> None:
    """Create a C++ enumeration header."""

    writer.write(f"enum class {task.name} : {task.instance['underlying']}")
    with writer.scope(suffix=";"):
        writer.join(
            *(
                enum_line(enum, value)
                for enum, value in task.instance.get("enum", {}).items()
            )
        )

    writer.write(
        (
            f"static_assert(sizeof({task.name}) == "
            f"{task.env.size(task.name)});"
        )
    )

    runtime = task.enum()

    writer.empty()

    if task.instance["identifier"]:
        writer.write(
            f"static constexpr enum_id_t {task.name}_id = {runtime.id};"
        )
        writer.empty()

    if runtime.default:
        writer.write(
            f"static constexpr auto {task.name}_default = "
            f"{task.name}::{task.instance['default']};"
        )
        writer.empty()

    enum_to_string_function(
        task, writer, task.instance["use_map"], definition=True
    )

    with writer.padding():
        writer.write(
            "inline std::ostream &operator<<(std::ostream &stream, "
            f"{task.name} instance)"
        )
        with writer.scope():
            writer.write("stream << to_string(instance);")
            writer.write("return stream;")

    string_to_enum_function(
        task, writer, task.instance["use_map"], definition=True
    )

    if task.instance["json"]:
        to_json_method(
            task,
            writer,
            runtime.asdict(),
            dumps_indent=task.instance["json_indent"],
            definition=True,
            inline=True,
        )


def enum_header(task: GenerateTask, writer: IndentedFileWriter) -> None:
    """Create a header file for an enumeration."""

    if task.is_cpp:
        cpp_enum_neader(task, writer)
    elif task.is_python:
        python_enum_header(task, writer)
