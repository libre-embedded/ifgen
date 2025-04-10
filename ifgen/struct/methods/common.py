"""
Utilities shared between struct methods.
"""

# third-party
from vcorelib.io import IndentedFileWriter

# internal
from ifgen.generation.interface import GenerateTask


def native_decode(writer: IndentedFileWriter) -> None:
    """Write a buffer decoding method for native byte order."""

    writer.write("auto buf = raw();")
    writer.write("*buf = *buffer;")


def native_encode(writer: IndentedFileWriter) -> None:
    """Write a buffer encoding method for native byte order."""

    writer.write("*buffer = *raw_ro();")


def wrapper_method(
    task: GenerateTask,
    writer: IndentedFileWriter,
    header: bool,
    is_encode: bool = True,
) -> None:
    """Create a generic encode/decode method."""

    method = task.cpp_namespace(
        "encode" if is_encode else "decode", header=header
    )

    if not header:
        writer.c_comment(f"'{method}' defined in header.")
        return

    line_start = f"inline std::size_t {method}("
    line = line_start + ("const " if not is_encode else "") + "Buffer *buffer,"

    writer.write(line)
    line = ""

    line += (
        (" " * len(line_start) if header else "") + "std::endian endianness = "
        f"std::endian::{task.instance['default_endianness']})"
    )

    if is_encode:
        line += " const"

    writer.write(line)

    with writer.scope():
        writer.write("std::size_t result = size;")

        with writer.padding():
            writer.write("if (endianness == std::endian::native)")

            with writer.scope():
                # Use trivial implementation for native encode and decode.
                if is_encode:
                    native_encode(writer)
                else:
                    native_decode(writer)

            writer.write("else")

            with writer.scope():
                writer.write(f"result = {method}_swapped(buffer);")

        writer.write("return result;")
