"""
A module implementing a unit-test output generator for structs.
"""

# third-party
from vcorelib.io import IndentedFileWriter

# internal
from ifgen.generation.interface import GenerateTask
from ifgen.generation.test import (
    unit_test_boilerplate,
    unit_test_main,
    unit_test_method,
    unit_test_method_name,
)


def assert_line(writer: IndentedFileWriter, data: str) -> None:
    """Write an assert line to the file."""
    writer.write(f"assert({data});")


def unit_test_stream_tests(
    task: GenerateTask, writer: IndentedFileWriter
) -> None:
    """Generate unit tests for stream interfaces."""

    writer.c_comment("Test stream interactions.")

    writer.write("static constexpr std::size_t len = 10;")
    writer.write(f"byte_array<{task.name}::size * len> streambuf;")
    writer.write(f"using TestSpan = byte_span<{task.name}::size * len>;")
    writer.write("auto stream = byte_spanstream(TestSpan(streambuf));")

    with writer.padding():
        writer.write("stream << dst;")
        writer.write("stream.seekg(0);")

    writer.write(f"{task.name} from_stream;")
    writer.write("stream >> from_stream;")


def unit_test_basic_method(
    task: GenerateTask, writer: IndentedFileWriter
) -> None:
    """
    Implement a simple encode-and-decode scenario with endianness as a
    function argument.
    """

    with unit_test_method("encode_decode_basic", task, writer):
        nspaced = task.name
        writer.write(f"{nspaced} src = {'{}'};")

        if task.instance["methods"]:
            assert_line(writer, f"src.span().size() == {nspaced}::size")
        else:
            writer.write("(void)src;")

        if task.instance["codec"]:
            writer.empty()
            writer.c_comment("Eventually, we could assign member values here.")

            with writer.padding():
                writer.write(f"{nspaced}::Buffer buffer;")
                assert_line(
                    writer,
                    f"src.encode<endianness>(&buffer) == {nspaced}::size",
                )

            writer.write(f"{nspaced} dst;")
            assert_line(
                writer, f"dst.decode<endianness>(&buffer) == {nspaced}::size"
            )
            assert_line(writer, "src == dst")

            writer.empty()
            writer.c_comment("Verify the values transferred.")
        else:
            writer.write("(void)endianness;")
            if task.instance["stream"]:
                writer.empty()
                writer.write(f"{nspaced} dst = {'{}'};")

        if task.instance["stream"]:
            writer.empty()
            unit_test_stream_tests(task, writer)


def unit_test_body(task: GenerateTask, writer: IndentedFileWriter) -> None:
    """Implement a unit test for a struct."""

    for method in ["encode_decode_basic"]:
        for arg in [
            "std::endian::native",
            "std::endian::little",
            "std::endian::big",
        ]:
            writer.write(f"{unit_test_method_name(method, task)}<{arg}>();")

        writer.empty()

    if task.instance["json"]:
        writer.c_comment("Attempt to decode this?")
        writer.write(f"std::cout << {task.name}::json();")


def create_struct_test(task: GenerateTask) -> None:
    """Create a unit test for the enum string-conversion methods."""

    if task.is_python:
        return

    if task.instance["unit_test"]:
        with unit_test_boilerplate(task, main=False) as writer:
            unit_test_basic_method(task, writer)

            writer.empty()

            with unit_test_main(task, writer):
                unit_test_body(task, writer)
