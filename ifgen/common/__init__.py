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


def endianness_single(writer: IndentedFileWriter) -> None:
    """Add methods for byte-sized primitives."""

    writer.c_comment("No action for byte-sized primitives.")
    writer.write(
        "template <std::endian endianness, byte_size T> "
        "inline void handle_endian_p(T *)"
    )
    with writer.scope():
        pass

    writer.write(
        "template <std::endian endianness, byte_size T> "
        "inline T handle_endian(T elem)"
    )
    with writer.scope():
        writer.write("return elem;")


def endianness_native(writer: IndentedFileWriter) -> None:
    """Add methods for native endianness (no swap)."""

    writer.c_comment("No action if endianness is native.")
    writer.write("template <std::endian endianness, std::integral T>")
    writer.write("inline void handle_endian_p(T *)")
    with writer.indented():
        writer.write(
            "requires(not byte_size<T>) && "
            "(endianness == std::endian::native)"
        )
    with writer.scope():
        pass

    writer.write("template <std::endian endianness, std::integral T>")
    writer.write("inline T handle_endian(T elem)")
    with writer.indented():
        writer.write(
            "requires(not byte_size<T>) && "
            "(endianness == std::endian::native)"
        )
    with writer.scope():
        writer.write("return elem;")


def endianness_integral(writer: IndentedFileWriter) -> None:
    """Add methods for integral types that require swapping."""

    writer.c_comment("Swap any integral type.")

    writer.write("template <std::endian endianness, std::integral T>")
    writer.write("inline T handle_endian(T elem)")
    with writer.indented():
        writer.write(
            "requires(not byte_size<T>) && (endianness != std::endian::native)"
        )
    with writer.scope():
        writer.write("return std::byteswap(elem);")

    writer.write("template <std::endian endianness, std::integral T>")
    writer.write("inline void handle_endian_p(T *elem)")
    with writer.indented():
        writer.write(
            "requires(not byte_size<T>) && (endianness != std::endian::native)"
        )
    with writer.scope():
        writer.write("*elem = std::byteswap(*elem);")


def endianness_enum(writer: IndentedFileWriter) -> None:
    """Add methods for enum types that require swapping."""

    writer.c_comment("Handler for enum class types.")
    writer.write("template <std::endian endianness, typename T>")
    writer.write("inline void handle_endian_p(T *elem)")
    with writer.indented():
        writer.write("requires(std::is_enum_v<T>)")
    with writer.scope():
        writer.write("using underlying = std::underlying_type_t<T>;")
        writer.write("handle_endian_p<endianness>(")
        with writer.indented():
            writer.write("reinterpret_cast<underlying *>(elem));")

    writer.write("template <std::endian endianness, typename T>")
    writer.write("inline T handle_endian(T elem)")
    with writer.indented():
        writer.write("requires(std::is_enum_v<T>)")
    with writer.scope():
        writer.write("return static_cast<T>(handle_endian<endianness>(")
        with writer.indented():
            writer.write("std::to_underlying(elem)));")


def endianness_float(writer: IndentedFileWriter) -> None:
    """Add methods for floating-point types that require swapping."""

    for width in ["32", "64"]:
        writer.empty()
        writer.c_comment(f"Handler for {width}-bit float.")
        writer.write(
            "template <std::endian endianness, std::floating_point T>"
        )
        writer.write("inline void handle_endian_p(T *elem)")

        prim = f"uint{width}_t"

        with writer.indented():
            writer.write(f"requires(sizeof(T) == sizeof({prim}))")
        with writer.scope():
            writer.write(
                f"handle_endian_p<endianness>"
                f"(reinterpret_cast<{prim} *>(elem));"
            )

        writer.write(
            "template <std::endian endianness, std::floating_point T>"
        )
        writer.write("inline T handle_endian(T elem)")
        with writer.indented():
            writer.write(f"requires(sizeof(T) == sizeof({prim}))")
        with writer.scope():
            writer.write("return std::bit_cast<T>(")
            with writer.indented():
                writer.write(
                    "handle_endian<endianness>"
                    f"(std::bit_cast<{prim}>(elem)));"
                )


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
        endianness_single(writer)

    endianness_native(writer)

    writer.empty()

    endianness_integral(writer)

    endianness_float(writer)

    writer.empty()

    endianness_enum(writer)


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

        writer.empty()
        writer.c_comment("Constraint for generated structs.")
        writer.write("template <typename T>")
        writer.write("concept ifgen_struct = requires")
        with writer.scope(suffix=";"):
            writer.write("std::is_integral_v<decltype(T::id)>;")
            writer.write("std::is_same_v<decltype(T::size), std::size_t>;")
