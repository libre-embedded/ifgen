"""
A module implementing Python struct-generation interfaces.
"""

# third-party
from vcorelib.io import IndentedFileWriter

# internal
from ifgen.generation.interface import GenerateTask


def python_struct_header(
    task: GenerateTask, writer: IndentedFileWriter
) -> None:
    """Create a Python module for a struct."""

    writer.empty()

    # need to sub-class 'runtimepy.codec.protocol.ProtocolFactory'
    # protocol = Protocol(EnumRegistry(), identifier=???, byte_order=???)
    # then just need to implement 'initialize' method

    # how nested structs work: assert that 'protocol' doesn't have attribute
    # for name of field, assign an .instance() of this field's protocol class
    # to that named attribute, add that protocol's array as a named
    # serializeable as well

    # should be able to test correctness with to_stream / from_stream etc.
    # (do this in runtimepy)

    del task
    writer.write("# todo")
