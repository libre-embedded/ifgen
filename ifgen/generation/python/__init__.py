"""
A module implementing code-generation interfaces for Python.
"""

# built-in
from contextlib import contextmanager
from typing import Iterable, Iterator

# third-party
from vcorelib.io import IndentedFileWriter

PythonImports = dict[str, list[str]]


def write_imports(
    writer: IndentedFileWriter,
    label: str,
    imports: PythonImports,
) -> None:
    """Write a group of Python imports to a file."""

    writer.empty()
    writer.write(f"# {label}")
    for key, values in sorted(imports.items()):
        writer.write(f"from {key} import {', '.join(values)}")


def python_imports(
    writer: IndentedFileWriter,
    built_in: PythonImports = None,
    third_party: PythonImports = None,
    internal: PythonImports = None,
    final_empty: int = 2,
) -> None:
    """Write Python-module imports."""

    if built_in:
        write_imports(writer, "built-in", built_in)
    if third_party:
        write_imports(writer, "third-party", third_party)
    if internal:
        write_imports(writer, "internal", internal)

    writer.empty(count=final_empty)


@contextmanager
def python_class(
    writer: IndentedFileWriter,
    name: str,
    docstring: str,
    parents: list[str] = None,
    final_empty: int = 2,
) -> Iterator[None]:
    """Write class definition contents."""

    line = f"class {name}"
    if parents:
        line += f"({', '.join(parents)})"
    line += ":"

    writer.write(line)
    with writer.indented():
        writer.write(f'"""{docstring}"""')
        writer.empty()
        yield

    writer.empty(count=final_empty)


@contextmanager
def python_function(
    writer: IndentedFileWriter,
    name: str,
    docstring: str,
    params: str = "",
    return_type: str = "None",
    final_empty: int = 2,
    decorators: Iterable[str] = None,
) -> Iterator[None]:
    """Write a Python function."""

    if decorators:
        for decorator in decorators:
            writer.write("@" + decorator)
    writer.write(f"def {name}({params}) -> {return_type}:")

    with writer.indented():
        writer.write(f'"""{docstring}"""')
        writer.empty()
        yield

    writer.empty(count=final_empty)
