"""
A module implementing a unit-test output generator for enums.
"""

# third-party
from vcorelib.io import IndentedFileWriter

# internal
from ifgen.generation.interface import GenerateTask
from ifgen.generation.test import unit_test_boilerplate


def test_single(
    task: GenerateTask, writer: IndentedFileWriter, enum: str
) -> None:
    """Generate test code for a single enumeration instance."""

    writer.empty()
    with_namespace = f"{task.name}::{enum}"
    writer.c_comment(f"Test {with_namespace}.")

    writer.write(f"std::cout << {with_namespace} << std::endl;")
    writer.write(f'assert(!strcmp(to_string({with_namespace}), "{enum}"));')
    writer.write(f'assert(from_string("{enum}", instance));')
    writer.write(f"assert(instance == {with_namespace});")


def unit_test_body(task: GenerateTask, writer: IndentedFileWriter) -> None:
    """Implement a simple unit test for the enumeration."""

    writer.write(f"{task.name} instance;")

    for enum in task.instance.get("enum", {}):
        test_single(task, writer, enum)

    if task.instance["json"]:
        writer.empty()
        writer.c_comment("Attempt to decode this?")
        writer.write(f"std::cout << {task.name}_json();")

    writer.empty()


def create_enum_test(task: GenerateTask) -> None:
    """Create a unit test for the enum string-conversion methods."""

    if task.is_python:
        return

    if task.instance["unit_test"]:
        with unit_test_boilerplate(task) as writer:
            unit_test_body(task, writer)
