"""
A module for generating shared headers and sources.
"""

# third-party
from vcorelib.io import IndentedFileWriter

# internal
from ifgen.generation.interface import GenerateTask
from ifgen.generation.test import unit_test_boilerplate


def create_common_test(task: GenerateTask) -> None:
    """Create a unit test for the enum string-conversion methods."""

    if task.is_python:
        return

    with unit_test_boilerplate(task, declare_namespace=True) as writer:
        writer.cpp_comment("TODO.")


def common_endianness(writer: IndentedFileWriter, task: GenerateTask) -> None:
    """Write endianness-related content."""

    writer.c_comment("Enforce that this isn't a mixed-endian system.")
    writer.write("static_assert(std::endian::native == std::endian::big or")
    writer.write("              std::endian::native == std::endian::little);")

    data = task.env.config.data
    endian = data["struct"]["default_endianness"]

    with writer.padding():
        writer.c_comment("Default endianness configured.")
        writer.write(
            f"static constexpr auto default_endian = std::endian::{endian};"
        )

    writer.c_comment("Detect primitives that don't need byte swapping.")
    writer.write("template <typename T>")
    writer.write("concept byte_size = sizeof(T) == 1;")

    with writer.padding():
        writer.c_comment("No action for byte-sized primitives.")
        writer.write(
            "template <byte_size T, std::endian endianness> "
            "inline void handle_endian(T *)"
        )
        with writer.scope():
            pass

    writer.c_comment("No action if endianness is native.")
    writer.write("template <std::integral T, std::endian endianness>")
    writer.write("inline void handle_endian(T *)")
    with writer.indented():
        writer.write(
            "requires(not byte_size<T>) && "
            "(endianness == std::endian::native)"
        )
    with writer.scope():
        pass

    writer.empty()

    writer.c_comment("Swap any integral type.")
    writer.write("template <std::integral T, std::endian endianness>")
    writer.write("inline void handle_endian(T *elem)")
    with writer.indented():
        writer.write(
            "requires(not byte_size<T>) && (endianness != std::endian::native)"
        )
    with writer.scope():
        writer.write("*elem = std::byteswap(*elem);")

    for width in ["32", "64"]:
        writer.empty()
        writer.c_comment(f"Handler for {width}-bit float.")
        writer.write(
            "template <std::floating_point T, std::endian endianness>"
        )
        writer.write("inline void handle_endian(T *elem)")
        with writer.indented():
            writer.write(f"requires(sizeof(T) == sizeof(uint{width}_t))")
        with writer.scope():
            writer.write(
                f"handle_endian<uint{width}_t, endianness>"
                f"(reinterpret_cast<uint{width}_t *>(elem));"
            )

    writer.empty()

    writer.c_comment("Handler for enum class types.")
    writer.write("template <typename T, std::endian endianness>")
    writer.write("inline void handle_endian(T *elem)")
    with writer.indented():
        writer.write("requires(std::is_enum_v<T>)")
    with writer.scope():
        writer.write("handle_endian<std::underlying_type_t<T>, endianness>(")
        with writer.indented():
            writer.write(
                "reinterpret_cast<std::underlying_type_t<T> *>(elem));"
            )


def create_common(task: GenerateTask) -> None:
    """Create a unit test for the enum string-conversion methods."""

    if task.is_python:
        return

    streams = task.stream_implementation

    includes = [
        "<bit>",
        "<concepts>",
        "<cstdint>",
        "<span>" if not streams else "<spanstream>",
        "<utility>",
    ]

    # probably get rid of everything besides the spanstream
    if streams:
        includes.extend(["<streambuf>", "<istream>", "<ostream>"])

    with task.boilerplate(includes=includes) as writer:
        common_endianness(writer, task)

        writer.empty()
        writer.c_comment("Configured primitives for identifiers.")
        data = task.env.config.data
        writer.write(f"using struct_id_t = {data['struct']['id_underlying']};")
        writer.write(f"using enum_id_t = {data['enum']['id_underlying']};")

        with writer.padding():
            writer.c_comment("Create useful aliases for bytes.")
            writer.write("template <std::size_t Extent = std::dynamic_extent>")
            writer.write("using byte_span = std::span<std::byte, Extent>;")
            writer.write(
                (
                    "template <std::size_t size> using byte_array = "
                    "std::array<std::byte, size>;"
                )
            )

        if streams:
            writer.c_comment("Abstract byte-stream interfaces.")
            writer.write("using byte_istream = std::basic_istream<std::byte>;")
            writer.write("using byte_ostream = std::basic_ostream<std::byte>;")

            writer.empty()
            writer.c_comment(
                "Concrete byte-stream interfaces (based on span)."
            )
            writer.write("using byte_spanbuf = std::basic_spanbuf<std::byte>;")
            writer.write(
                "using byte_spanstream = std::basic_spanstream<std::byte>;"
            )
