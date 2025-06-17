"""
A module defining generator interfaces.
"""

# built-in
from contextlib import ExitStack, contextmanager
from json import dumps
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator, NamedTuple, Optional

# third-party
from runtimepy.codec.protocol import Protocol
from runtimepy.enum import RuntimeEnum
from vcorelib.io import IndentedFileWriter
from vcorelib.namespace import CPP_DELIM
from vcorelib.paths.context import TextPreprocessor

# internal
from ifgen import PKG_NAME, VERSION
from ifgen.enums import Generator, Language
from ifgen.environment import IfgenEnvironment
from ifgen.paths import audit_init_file

InstanceConfig = dict[str, Any]
IfgenConfig = dict[str, Any]


class TypeLookup(NamedTuple):
    """A container for type-lookup results."""

    name: str
    final: str
    generator: Generator


def apply_cpp_namespace(
    name: str, data: str, header: bool = True, prefix: str = None
) -> str:
    """Namespace a string with this task's name."""

    if not header:
        data = f"{name}::{data}"
    return data if not prefix else prefix + data


@contextmanager
def ifndef_guard(writer: IndentedFileWriter, text: str) -> Iterator[None]:
    """Guard contents with header macro convention."""

    writer.write(f"#ifndef {text}")
    writer.write(f"#define {text}")
    try:
        yield
    finally:
        writer.empty()
        writer.write("#endif")


class GenerateTask(NamedTuple):
    """A container for instance-generation tasks."""

    name: str
    generator: Generator
    language: Language

    path: Path
    test_path: Path

    instance: InstanceConfig
    env: IfgenEnvironment

    def cpp_namespace(
        self, data: str, header: bool = True, prefix: str = None
    ) -> str:
        """Namespace a string with this task's name."""

        return apply_cpp_namespace(
            self.name, data, header=header, prefix=prefix
        )

    @property
    def is_python(self) -> bool:
        """Determine if this task's language is set to Python."""
        return self.language is Language.PYTHON

    @property
    def is_cpp(self) -> bool:
        """Determine if this task's language is set to C++."""
        return self.language is Language.CPP

    @property
    def stream_implementation(self) -> bool:
        """
        Determine if this instances should include a stream implementations.
        """
        return self.instance.get("stream", True)  # type: ignore

    @property
    def source_path(self) -> Path:
        """Get a source file for this task."""
        return self.path.with_suffix(f".{self.language.source_suffix}")

    @property
    def config(self) -> IfgenConfig:
        """Get the environment's configuration data."""
        return self.env.config.data

    def enum(self) -> RuntimeEnum:
        """Look up a runtime enumeration for this task."""

        return self.env.get_enum(self.name)

    def protocol(self) -> Protocol:
        """Loop up a protocol for this task."""

        return self.env.get_protocol(self.name)

    def namespace(self, *names: str) -> str:
        """Get this task's namespace."""

        nspace = self.env.types.root_namespace
        with nspace.pushed(*self.instance.get("namespace", []), *names):
            result = nspace.namespace(track=False)

        assert result, f"No namespace for '{self.name}'!"
        return result

    def check_custom_type(self, name: str) -> Optional[TypeLookup]:
        """Check if a name refers to a custom type."""

        final = name.split(CPP_DELIM)[-1]

        result = None
        for gen in Generator:
            if final in self.config.get(gen.value, {}):
                result = TypeLookup(name, final, gen)
                break
        return result

    def custom_include(self, name: str) -> Optional[Path]:
        """Attempt to build a path to a custom include."""

        result = None

        lookup = self.check_custom_type(name)
        if lookup is not None:
            result = (
                Path(
                    "..",
                    self.env.make_path(
                        lookup.final, lookup.generator, self.language
                    ),
                )
                if lookup.generator != self.generator
                else Path(f"{lookup.final}.{self.language.header_suffix}")
            )

        return result

    def command(self, command: str, data: str = "", space: str = " ") -> str:
        """Get a doxygen command string."""
        return (
            str(self.config["command"])
            + command
            + (space if data else "")
            + data
        )

    @contextmanager
    def source_boilerplate(
        self, includes: Iterable[str]
    ) -> Iterator[IndentedFileWriter]:
        """Create standard generation boilerplate for a source file."""

        with ExitStack() as stack:
            writer = stack.enter_context(
                IndentedFileWriter.from_path_if_different(
                    self.source_path,
                    per_indent=4,
                    preprocessor=self._text_preprocessor(),
                )
            )

            self.javadoc_header(writer)

            include = self.env.rel_include(
                self.name, self.generator, self.language
            )
            self.write_includes(
                writer,
                includes=[f'"{include}"'] + list(includes),
            )

            self.handle_namespace(stack, writer)

            yield writer

    def javadoc_header(
        self, writer: IndentedFileWriter, json: bool = False
    ) -> None:
        """Write a standard file header."""

        description = f"Generated by {PKG_NAME} ({VERSION})."

        with ExitStack() as stack:
            if self.is_python:
                stack.enter_context(
                    writer.scope(opener='"""', closer='"""', indent=0)
                )
                writer.write(description)
            else:
                stack.enter_context(writer.javadoc())
                writer.write(self.command("file"))
                writer.write(self.command("brief", description))

            if json:
                writer.write(dumps(self.instance, indent=2))

    def handle_namespace(
        self, stack: ExitStack, writer: IndentedFileWriter
    ) -> None:
        """Write namespace boilerplate to a file."""

        if self.is_python:
            return

        # Write namespace.
        namespace = self.namespace()
        writer.write(f"namespace {namespace}")

        stack.enter_context(
            writer.scope(suffix=f"; // namespace {namespace}", indent=0)
        )

        stack.enter_context(writer.padding())

    def write_includes(
        self, writer: IndentedFileWriter, includes: Iterable[str] = None
    ) -> None:
        """Write sorted includes to a file."""

        if self.is_python:
            return

        with writer.padding():
            for include in sorted(includes if includes else []):
                if include:
                    writer.write(f"#include {include}")

    def resolve_description(
        self, description: Optional[str] = None
    ) -> Optional[str]:
        """Attempt to resolve a config-driven description."""

        if description is None:
            if "description" in self.instance and self.instance["description"]:
                description = self.instance["description"]

        return description

    def _text_preprocessor(self) -> Optional[TextPreprocessor]:
        """
        Get a text preprocessing method (i.e. code formatting) for this task.
        """
        return self.env.preprocessors.get(self.language)

    @contextmanager
    def boilerplate(
        self,
        includes: Iterable[str] = None,
        is_test: bool = False,
        use_namespace: bool = True,
        description: Optional[str] = None,
        json: bool = False,
        parent_depth: int = 0,
    ) -> Iterator[IndentedFileWriter]:
        """
        Create standard generation boilerplate and yield the file writer to
        use for writing the remaining content.
        """

        path = self.path if not is_test else self.test_path

        if self.is_python:
            audit_init_file(path, parent_depth=parent_depth)

        with ExitStack() as stack:
            writer = stack.enter_context(
                IndentedFileWriter.from_path_if_different(
                    path, per_indent=4, preprocessor=self._text_preprocessor()
                )
            )

            # Write file header.
            self.javadoc_header(writer, json=json)

            if self.is_cpp:
                writer.empty()
                if not is_test:
                    writer.write("#pragma once")
                    stack.enter_context(
                        ifndef_guard(
                            writer,
                            "_".join(
                                [
                                    x.upper()
                                    for x in [
                                        self.namespace().replace("::", "_"),
                                        path.parent.name,
                                        self.path.name.replace(".", "_"),
                                    ]
                                ]
                            ),
                        )
                    )
                else:
                    writer.write("#ifdef NDEBUG")
                    writer.write("#undef NDEBUG")
                    writer.write("#endif")

            self.write_includes(writer, includes=includes)

            if use_namespace:
                self.handle_namespace(stack, writer)

            if not self.is_python:
                description = self.resolve_description(description=description)
                if description:
                    with writer.javadoc():
                        writer.write(description)

            yield writer

    def has_instances(self) -> bool:
        """Determine whether or not this instance has concrete instances."""
        return bool(self.instance.get("instances", []))

    def method_suffix(self) -> str:
        """Get a possible suffix for a method."""
        return "" if not self.has_instances() else " volatile"


InstanceGenerator = Callable[[GenerateTask], None]
