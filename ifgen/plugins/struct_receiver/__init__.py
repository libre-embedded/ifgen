"""
A struct-receiver interface implementation.
"""

# third-party
from vcorelib.io.file_writer import IndentedFileWriter

# internal
from ifgen.generation.interface import GenerateTask
from ifgen.generation.python import python_imports
from ifgen.struct.python import python_dependencies


def python_struct_receiver(
    task: GenerateTask, writer: IndentedFileWriter
) -> None:
    """Python struct receiver generation."""

    structs: list[str] = list(task.env.config.data.get("structs", {}))

    python_imports(
        writer,
        third_party={"runtimepy.codec.protocol.receiver": ["StructReceiver"]},
        internal=python_dependencies([], structs, struct_prefix="..structs"),
        final_empty=1,
    )

    writer.write("RECEIVER = StructReceiver(")
    with writer.indented():
        for struct in structs:
            writer.write(struct + ",")
    writer.write(")")


def cpp_struct_receiver(
    task: GenerateTask, writer: IndentedFileWriter
) -> None:
    """C++ struct receiver generation."""

    print(f"(test1) {task.name} {task.instance}")
    writer.cpp_comment("cpp impl")
