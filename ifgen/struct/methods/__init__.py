"""
A module implementing interfaces for generating struct method code.
"""

# built-in
from typing import Any

# third-party
from vcorelib.io import IndentedFileWriter

# internal
from ifgen.generation.interface import GenerateTask
from ifgen.generation.json import to_json_method
from ifgen.struct.methods.common import swap_fields


def protocol_json(task: GenerateTask) -> dict[str, Any]:
    """Get JSON data for this struct task."""

    protocol = task.protocol()

    # use something better for this

    return protocol.export_json()


def span_method(
    task: GenerateTask, writer: IndentedFileWriter, header: bool
) -> None:
    """Generate a span method."""

    if not header:
        writer.c_comment("Span method defined in header.")
        return

    with writer.javadoc():
        writer.write(("Get this instance as a byte span."))

    span_type = task.cpp_namespace("Span", header=header)
    method = task.cpp_namespace("span", header=header)

    writer.write(f"inline {span_type} {method}()")

    with writer.scope():
        writer.write("return Span(*raw());")


def struct_buffer_method(
    task: GenerateTask,
    writer: IndentedFileWriter,
    header: bool,
    read_only: bool,
) -> None:
    """Generate a method for raw buffer access."""

    if not header:
        return

    with writer.javadoc():
        writer.write(
            (
                "Get this instance as a "
                f"{'read-only ' if read_only else ''}"
                "fixed-size byte array."
            )
        )

    buff_type = task.cpp_namespace("Buffer", header=header)

    if read_only:
        buff_type = "const " + buff_type

    # Returns a pointer.
    method = task.cpp_namespace(
        "raw()" if not read_only else "raw_ro()", prefix="*", header=header
    )
    writer.write(
        f"inline {buff_type} {method}" + (" const" if read_only else "")
    )

    with writer.scope():
        writer.write(
            "return reinterpret_cast"
            f"<{'const ' if read_only else ''}Buffer *>(this);"
        )


def endian_str(task: GenerateTask) -> str:
    """Get the appropriate default endian argument for this struct."""

    return (
        f"std::endian::{task.instance['default_endianness']}"
        if task.instance["default_endianness"]
        != task.env.config.data["struct"]["default_endianness"]
        else "default_endian"
    )


def encode_endian(task: GenerateTask, writer: IndentedFileWriter) -> None:
    """Write a struct method for encoding buffers."""

    with writer.javadoc():
        writer.write("Encode this instance to a buffer.")
        writer.empty()
        writer.write(
            task.command(
                "tparam",
                "    endianness Byte order for encoding elements.",
            )
        )
        writer.write(task.command("param[out]", "buffer     Buffer to write."))
        writer.write(
            task.command(
                "return", "               The number of bytes encoded."
            )
        )

    writer.write(f"template <std::endian endianness = {endian_str(task)}>")
    writer.write("inline std::size_t encode(Buffer *buffer) const")
    with writer.scope():
        writer.c_comment("Check if buffer is external.")
        writer.write("auto this_ro = raw_ro();")
        writer.write("if (buffer != this_ro)")
        with writer.scope():
            writer.write("*buffer = *this_ro;")

        with writer.padding():
            writer.c_comment("Handle byte swapping if necessary.")
            writer.write("if (endianness != std::endian::native)")
            with writer.scope():
                writer.write(
                    f"auto other = reinterpret_cast<{task.name} *>(buffer);"
                )
                writer.write("(void)other;")
                swap_fields(task, writer, elem_prefix="other->")

        writer.write("return size;")


def decode_endian(task: GenerateTask, writer: IndentedFileWriter) -> None:
    """Write a struct method for decoding buffers."""

    with writer.javadoc():
        writer.write("Update this instance from a buffer.")
        writer.empty()
        writer.write(
            task.command(
                "tparam",
                "   endianness Byte order from decoding elements.",
            )
        )
        writer.write(task.command("param[in]", "buffer     Buffer to read."))
        writer.write(
            task.command(
                "return", "              The number of bytes decoded."
            )
        )

    writer.write(f"template <std::endian endianness = {endian_str(task)}>")
    writer.write("inline std::size_t decode(const Buffer *buffer)")
    with writer.scope():
        writer.c_comment("Check if buffer is external.")
        writer.write("auto this_raw = raw();")
        writer.write("if (this_raw != buffer)")
        with writer.scope():
            writer.write("*this_raw = *buffer;")

        with writer.padding():
            writer.c_comment("Handle byte swapping if necessary.")
            writer.write("if (endianness != std::endian::native)")
            with writer.scope():
                swap_fields(task, writer)

        writer.write("return size;")


def encode_decode_endian(
    task: GenerateTask, writer: IndentedFileWriter
) -> None:
    """Write struct methods for encoding and decoding buffers."""

    encode_endian(task, writer)
    writer.empty()
    decode_endian(task, writer)


def struct_methods(
    task: GenerateTask, writer: IndentedFileWriter, header: bool
) -> None:
    """Write generated-struct methods."""

    if header:
        writer.write("using Buffer = byte_array<size>;")
        writer.write("using Span = byte_span<size>;")
        with writer.padding():
            writer.write(
                f"auto operator<=>(const {task.name} &) const = default;"
            )

    struct_buffer_method(task, writer, header, False)

    if header:
        writer.empty()

    span_method(task, writer, header)

    if header:
        writer.empty()

    struct_buffer_method(task, writer, header, True)

    if task.instance["codec"] and header:
        writer.empty()
        encode_decode_endian(task, writer)

    if task.instance["json"]:
        to_json_method(
            task,
            writer,
            protocol_json(task),
            dumps_indent=task.instance["json_indent"],
            task_name=False,
            static=True,
            definition=header,
        )
