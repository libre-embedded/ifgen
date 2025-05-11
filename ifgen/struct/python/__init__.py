"""
A module implementing Python struct-generation interfaces.
"""

# built-in
from typing import Any

# third-party
from runtimepy.codec.system import TypeSystem
from vcorelib.io import IndentedFileWriter
from vcorelib.names import to_snake

# internal
from ifgen.enum.python import strip_t_suffix
from ifgen.generation.interface import GenerateTask
from ifgen.generation.python import (
    PythonImports,
    python_class,
    python_function,
    python_imports,
)
from ifgen.struct.util import struct_dependencies


def cpp_ns_final(data: str) -> str:
    """Get only the final string in a C++ style namespace string."""
    return data.split("::")[-1]


def python_enums_structs(task: GenerateTask) -> tuple[list[str], list[str]]:
    """Get enum and struct dependency information for this task."""

    enums = []
    structs = []

    types = task.env.types
    for dep in struct_dependencies(task):
        dep = strip_t_suffix(dep)

        if dep in types.primitives:
            continue

        if types.is_enum(dep):
            enums.append(dep)
            continue

        if types.is_custom(dep):
            structs.append(dep)

    return sorted(enums), sorted(structs)


def python_dependencies(
    enums: list[str],
    structs: list[str],
    enum_prefix: str = "..enums",
    struct_prefix: str = "",
) -> PythonImports:
    """
    Get the names of external (to the module being generated) dependencies
    by type.
    """

    deps: PythonImports = {}

    for enum in enums:
        enum = cpp_ns_final(enum)
        deps[f"{enum_prefix}.{to_snake(enum)}"] = [enum]
    for struct in structs:
        struct = cpp_ns_final(struct)
        deps[f"{struct_prefix}.{to_snake(struct)}"] = [struct]

    return deps


def python_struct_field(
    writer: IndentedFileWriter,
    types: TypeSystem,
    field: dict[str, Any],
    structs: list[str],
    enums: list[str],
) -> None:
    """Write lines for a struct field."""

    writer.write("protocol.add_field(")

    kind = strip_t_suffix(field["type"])

    with writer.indented():
        line = f"\"{field['name']}\","
        if field.get("description"):
            line += f"  # {field['description']}"
        writer.write(line)

        if kind in types.primitives:
            writer.write(f'kind="{kind}",')

        elif kind in structs:
            writer.write("serializable=" f"{cpp_ns_final(kind)}.instance(),")

        elif kind in enums:
            writer.write(f'enum="{cpp_ns_final(kind)}",')

        if "array_length" in field:
            writer.write(f"array_length={field['array_length']},")

    writer.write(")")


def python_struct_fields(
    task: GenerateTask,
    writer: IndentedFileWriter,
    structs: list[str],
    enums: list[str],
) -> None:
    """Write protocol initialization code."""

    types = task.env.types

    # 'alternates' field not handled yet.

    for field in task.instance["fields"]:
        if "fields" in field:
            writer.write(
                "with protocol.add_bit_fields"
                f'("{field["name"]}", '
                f'kind="{strip_t_suffix(field["type"])}") as fields:'
            )
            with writer.indented():
                for bit_field in field["fields"]:
                    line = ""

                    if bit_field["width"] == 1:
                        line = "fields.flag("
                        line += f"\"{bit_field['name']}\", "
                    else:
                        line = "fields.field("
                        line += (
                            f"\"{bit_field['name']}\", "
                            f"{bit_field['width']}, "
                        )

                    if bit_field.get("description"):
                        line += f"description=\"{bit_field['description']}\", "

                    kind = bit_field.get("type")
                    if kind and kind in enums:
                        line += f'enum="{cpp_ns_final(kind)}", '

                    line += f"index={bit_field['index']}"

                    writer.write(line + ")")

        else:
            python_struct_field(writer, types, field, structs, enums)


def python_struct_header(
    task: GenerateTask, writer: IndentedFileWriter
) -> None:
    """Create a Python module for a struct."""

    enums, structs = python_enums_structs(task)

    python_imports(
        writer,
        third_party={
            "runtimepy.codec.protocol": ["Protocol", "ProtocolFactory"],
            "runtimepy.primitives.byte_order": ["STD_ENDIAN", "enum_registry"],
        },
        internal=python_dependencies(enums, structs),
    )

    proto = task.protocol()

    id_underlying = strip_t_suffix(
        task.env.config.data["struct"]["id_underlying"]
    )

    with python_class(
        writer,
        task.name,
        task.resolve_description() or "No description.",
        parents=["ProtocolFactory"],
        final_empty=0,
    ):
        # Create protocol instance.
        writer.write("protocol = Protocol(")
        with writer.indented():
            writer.write(
                f"enum_registry({', '.join(cpp_ns_final(x) for x in enums)}),"
            )
            writer.write(f"identifier={proto.id},")
            writer.write("identifier_primitive=" f'"{id_underlying}",')
            writer.write(
                "byte_order=STD_ENDIAN"
                f"[\"{task.instance['default_endianness']}\"],"
            )
        writer.write(")")

        writer.empty()

        with python_function(
            writer,
            "initialize",
            "Initialize this protocol.",
            params="cls, protocol: Protocol",
            decorators=["classmethod"],
            final_empty=0,
        ):
            python_struct_fields(task, writer, structs, enums)
