"""
A struct-receiver interface implementation.
"""

# built-in
from typing import Any

# third-party
from vcorelib.io.arbiter import ARBITER
from vcorelib.names import to_snake
from vcorelib.paths import rel

# internal
from ifgen.enums import Language
from ifgen.generation.interface import GenerateTask
from ifgen.generation.python import python_imports
from ifgen.struct import header_for_type
from ifgen.struct.python import python_dependencies


def python_struct_receiver(task: GenerateTask) -> None:
    """Python struct receiver generation."""

    structs: list[str] = list(task.env.config.data.get("structs", {}))

    with task.boilerplate(json=False, parent_depth=2) as writer:
        python_imports(
            writer,
            third_party={
                "runtimepy.codec.protocol.receiver": ["StructReceiver"]
            },
            internal=python_dependencies(
                [], structs, struct_prefix="..structs"
            ),
            final_empty=1,
        )

        writer.write("RECEIVER = StructReceiver(")
        with writer.indented():
            for struct in structs:
                writer.write(struct + ",")
        writer.write(")")

    runtimepy_structs: list[Any] = []
    for struct in structs:
        snake = to_snake(struct)
        runtimepy_structs.append(
            {
                "name": snake,
                "config": {
                    "protocol_factory": ".".join(
                        list(
                            rel(
                                task.env.directories[Language.PYTHON].output,
                                base=task.env.root_path,
                            ).parts
                        )
                        + ["structs", snake, struct]
                    )
                },
            }
        )

    assert ARBITER.encode(
        task.path.with_suffix(".yaml"), {"structs": runtimepy_structs}
    )[0]


# pylint: disable=too-many-statements
def cpp_struct_receiver(task: GenerateTask) -> None:
    """C++ struct receiver generation."""

    data = task.env.config.data
    structs: list[str] = list(
        x for x in data.get("structs", {}) if data["structs"][x]["codec"]
    )

    names_qualified = {}
    for struct in structs:
        names = data["structs"][struct].get("namespace", [])
        names.append(struct)
        names_qualified[struct] = "::".join(names)

    with task.boilerplate(
        json=False,
        includes=["<functional>"]
        + [header_for_type(x, task) for x in structs],
        parent_depth=2,
    ) as writer:
        writer.write("template <ifgen_struct T>")
        writer.write("using struct_handler = std::function<void(const T &)>;")
        writer.empty()

        writer.write("using non_struct_handler =")
        with writer.indented():
            writer.write(
                "std::function<std::size_t(const std::byte *, std::size_t)>;"
            )
        writer.empty()

        writer.write("struct StructReceiver")
        with writer.scope(suffix=";"):
            for struct in structs:
                snake = to_snake(struct)
                writer.write(f"{names_qualified[struct]} {snake};")
                writer.write(
                    f"struct_handler<decltype({snake})> "
                    f"{snake}_handler = nullptr;"
                )
                writer.empty()

            writer.write("non_struct_handler non_struct = nullptr;")
            writer.empty()

            writer.write("std::size_t dropped_messages = 0;")
            writer.write("std::size_t dropped_bytes = 0;")
            writer.empty()

            writer.write("inline void drop_message(std::size_t &len)")
            with writer.scope():
                writer.write("if (len)")
                with writer.scope():
                    writer.write("dropped_messages++;")
                    writer.write("dropped_bytes += len;")
                    writer.write("len = 0;")

            writer.empty()
            writer.write("template <std::endian endianness = default_endian>")
            writer.write(
                "void handle_message(const std::byte *data, std::size_t len)"
            )
            with writer.scope():
                writer.write("if (len < sizeof(struct_id_t))")
                with writer.scope():
                    writer.write("drop_message(len);")
                    writer.write("return;")

                writer.empty()

                writer.c_comment("Read identifier and advance buffer.")
                writer.write(
                    "struct_id_t ident = "
                    "handle_endian<struct_id_t, endianness>("
                )
                with writer.indented():
                    writer.write(
                        "*reinterpret_cast<const struct_id_t *>(data));"
                    )
                writer.write("data += sizeof(struct_id_t);")
                writer.write("len -= sizeof(struct_id_t);")

                writer.empty()

                writer.write("switch (ident)")
                writer.write("{")

                writer.write("case 0:")
                with writer.indented():
                    writer.write("if (non_struct)")
                    with writer.scope():
                        writer.write("auto result = non_struct(data, len);")
                        writer.write("if (result)")
                        with writer.scope():
                            writer.write("data += result;")
                            writer.write("len -= result;")
                        writer.write("else")
                        with writer.scope():
                            writer.write("drop_message(len);")

                    writer.write("else")
                    with writer.scope():
                        writer.write("drop_message(len);")

                    writer.write("break;")

                for struct in structs:
                    snake = to_snake(struct)
                    writer.write(f"case decltype({snake})::id:")
                    with writer.indented():
                        writer.write(f"if (len >= decltype({snake})::size)")
                        with writer.scope():
                            writer.write(f"if ({snake}_handler)")
                            with writer.scope():
                                writer.write(f"{snake}.decode<endianness>(")
                                with writer.indented():
                                    writer.write(
                                        f"reinterpret_cast<const decltype"
                                        f"({snake}) *>(data)->raw_ro());"
                                    )
                                writer.write(f"{snake}_handler({snake});")

                            writer.write(f"data += decltype({snake})::size;")
                            writer.write(f"len -= decltype({snake})::size;")

                        writer.write("else")
                        with writer.scope():
                            writer.write("drop_message(len);")

                        writer.write("break;")

                writer.write("default:")
                with writer.indented():
                    writer.c_comment("Couldn't match any identifier.")
                    writer.write("drop_message(len);")
                writer.write("}")

                writer.empty()

                writer.c_comment("Continue if more bytes remain.")
                writer.write("if (len)")
                with writer.scope():
                    writer.write("handle_message<endianness>(data, len);")
