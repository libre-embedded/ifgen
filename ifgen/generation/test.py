"""
A module implementing unit-testing related generation utilities.
"""

# built-in
from contextlib import ExitStack, contextmanager
from os import linesep
from typing import Iterator

# third-party
from vcorelib.io import IndentedFileWriter

# internal
from ifgen.generation.interface import GenerateTask


def unit_test_method_name(name: str, task: GenerateTask) -> str:
    """Get the name of a unit test."""
    return f"test_{task.name}_{name}"


@contextmanager
def unit_test_method(
    name: str, task: GenerateTask, writer: IndentedFileWriter
) -> Iterator[None]:
    """Generate unit-test method boilerplate."""

    writer.write("template <std::endian endianness>")
    writer.write(f"void {unit_test_method_name(name, task)}(void)")
    with writer.scope():
        nspace = task.env.types.root_namespace

        project_wide = nspace.namespace(track=False)
        writer.write(f"using namespace {project_wide};")

        with nspace.pushed(*task.instance.get("namespace", [])):
            curr = nspace.namespace(track=False)
            if curr != project_wide:
                writer.write(f"using namespace {curr};")

        writer.empty()
        yield


@contextmanager
def unit_test_main(
    task: GenerateTask, writer: IndentedFileWriter, description: bool = True
) -> Iterator[None]:
    """A method for generating main-function boilerplate for unit tests."""

    if description:
        with writer.javadoc():
            writer.write(f"A unit test for {task.generator} {task.name}.")
            writer.empty()
            writer.write("\\return 0 on success.")

    writer.write("int main(void)")
    with writer.scope():
        writer.write(f"using namespace {task.namespace()};")
        writer.empty()
        yield
        writer.write("return 0;")


@contextmanager
def unit_test_boilerplate(
    task: GenerateTask,
    includes: list[str] = None,
    main: bool = True,
    declare_namespace: bool = False,
) -> Iterator[IndentedFileWriter]:
    """Handle standard unit-test boilerplate."""

    include = task.env.rel_include(task.name, task.generator, task.language)

    if includes is None:
        includes = []

    linesep.join([f"A unit test for {task.generator} {task.name}."])

    with ExitStack() as stack:
        writer = stack.enter_context(
            task.boilerplate(
                includes=[
                    "<cassert>",
                    "<cstring>",
                    "<iostream>",
                    f'"{include}"',
                ]
                + includes,
                is_test=True,
                use_namespace=False,
            )
        )

        if declare_namespace:
            writer.write(f"namespace {task.namespace()}")
            with writer.scope(suffix=";"):
                writer.c_comment(
                    (
                        "Declared to ensure this namespace "
                        "has been declared in general."
                    )
                )
            writer.empty()

        if main:
            stack.enter_context(unit_test_main(task, writer))

        yield writer
