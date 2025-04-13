"""
A module for generating shared headers and sources.
"""

# internal
from ifgen.generation.interface import GenerateTask
from ifgen.generation.test import unit_test_boilerplate


def create_common_test(task: GenerateTask) -> None:
    """Create a unit test for the enum string-conversion methods."""

    if task.is_python:
        return

    with unit_test_boilerplate(task, declare_namespace=True) as writer:
        writer.cpp_comment("TODO.")


def create_common(task: GenerateTask) -> None:
    """Create a unit test for the enum string-conversion methods."""

    if task.is_python:
        return

    streams = task.stream_implementation

    includes = [
        "<cstdint>",
        "<bit>",
        "<span>" if not streams else "<spanstream>",
        "<utility>",
    ]

    # probably get rid of everything besides the spanstream
    if streams:
        includes.extend(["<streambuf>", "<istream>", "<ostream>"])

    with task.boilerplate(includes=includes) as writer:
        writer.c_comment("Enforce that this isn't a mixed-endian system.")
        writer.write(
            "static_assert(std::endian::native == std::endian::big or"
        )
        writer.write(
            "              std::endian::native == std::endian::little);"
        )

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
