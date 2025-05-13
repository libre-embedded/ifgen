"""
A module implementing a generation-environment interface.
"""

# built-in
from pathlib import Path
from typing import Any, NamedTuple, Optional

# third-party
from runtimepy.codec.protocol import Protocol
from runtimepy.codec.system import TypeSystem
from runtimepy.enum import RuntimeEnum
from vcorelib.logging import LoggerMixin
from vcorelib.names import to_snake
from vcorelib.paths import normalize, prune_empty_directories
from vcorelib.paths.context import TextPreprocessor

# internal
from ifgen import PKG_NAME
from ifgen.config import Config
from ifgen.enums import Generator, Language
from ifgen.environment.field import process_field
from ifgen.environment.padding import PaddingManager, type_string
from ifgen.paths import combine_if_not_absolute, create_formatter


def runtime_enum_data(data: dict[str, Any]) -> dict[str, int]:
    """Get runtime enumeration data."""

    result = {}

    curr_value = 0

    for key, value in data.items():
        if value is None or "value" not in value:
            result[key] = curr_value
            curr_value += 1
        else:
            result[key] = value["value"]
            if value["value"] >= curr_value:
                curr_value = value["value"] + 1

    return result


class Directories(NamedTuple):
    """A collection of directories relevant to code generation outputs."""

    config_parts: list[str]
    source: Path
    output: Path
    test_dir: Path

    def prune_empty(self) -> None:
        """Attempt to eliminate any empty output directories."""

        for path in (self.source, self.output, self.test_dir):
            prune_empty_directories(path)


class IfgenEnvironment(LoggerMixin):
    """A class for managing stateful information while generating outputs."""

    def __init__(self, root: Path, config: Config) -> None:
        """Initialize this instance."""

        super().__init__()
        self.root_path = root
        self.config = config

        # Load per-language directories.
        self.directories: dict[Language, Directories] = {}
        for language in Language:
            result = self.get_dirs(language)
            if result is not None:
                self.directories[language] = result

        self.generated: set[Path] = set()

        # Create output directories.
        for language, dirs in self.directories.items():
            for subdir in Generator:
                for path in [dirs.output, dirs.test_dir]:
                    path.joinpath(subdir).mkdir(parents=True, exist_ok=True)

        self.types = TypeSystem(
            *(
                self.config.data["namespace"]
                if self.config.data["namespace"]
                else [PKG_NAME.capitalize()]
            )
        )
        self.padding = PaddingManager()
        self._register_enums()
        self._register_structs()

        # Set up language-specific preprocessors.
        self.preprocessors: dict[Language, TextPreprocessor] = {
            Language.CPP: create_formatter(
                self.config.data["clang_format"], cwd=self.root_path
            )
        }

    def prune_empty(self) -> None:
        """Attempt to eliminate any empty output directories."""

        for dirs in self.directories.values():
            dirs.prune_empty()

    def get_dirs(self, langauge: Language) -> Optional[Directories]:
        """Get source, output and test directories."""

        result = None

        cfg_dir = langauge.cfg_dir_name
        if cfg_dir in self.config.data:
            dirs = self.config.data[cfg_dir]
            if dirs:
                source = combine_if_not_absolute(
                    self.root_path, normalize(*dirs)
                )
                output = combine_if_not_absolute(
                    source,
                    (
                        normalize(*self.config.data["output_dir"])
                        if self.config.data["output_dir"]
                        else ""
                    ),
                )
                test_dir = combine_if_not_absolute(
                    source,
                    (
                        normalize(*self.config.data["test_dir"])
                        if self.config.data["test_dir"]
                        else ""
                    ),
                )
                result = Directories(dirs, source, output, test_dir)

        return result

    def _register_enums(self) -> None:
        """Register configuration enums."""

        for name, enum in self.config.data.get("enums", {}).items():
            self.types.enum(
                name,
                runtime_enum_data(enum["enum"]),
                *enum["namespace"],
                primitive=type_string(enum["underlying"]),
                default=enum.get("default"),
            )

            self.logger.info(
                "Registered enum '%s'.",
                self.types.root_namespace.delim.join(
                    enum["namespace"] + [name]
                ),
            )

    def _register_structs(self) -> None:
        """Register configuration structs."""

        for name, struct in self.config.data.get("structs", {}).items():
            namespace = [*struct["namespace"]]
            self.types.register(name, *namespace)

            field_groups = []

            self.padding.reset()
            for field in struct["fields"]:
                padding = list(
                    process_field(
                        name, self.padding, self.types, field, namespace
                    )
                )
                if padding:
                    field_groups.append(padding)
                field_groups.append([field])

            # Re-assign fields structure.
            struct["fields"] = []
            for group in field_groups:
                for field in group:
                    struct["fields"].append(field)

            self.logger.info(
                "Registered struct '%s' (%d bytes).",
                self.types.root_namespace.delim.join(
                    struct["namespace"] + [name]
                ),
                self.types.size(name, *struct["namespace"]),
            )

    def make_path(
        self,
        name: str,
        generator: Generator,
        language: Language,
        from_output: bool = False,
        track: bool = True,
    ) -> Path:
        """Make part of a task's path."""

        if language is Language.PYTHON:
            name = to_snake(name)

        result = Path(str(generator), f"{name}.{language.header_suffix}")

        if from_output:
            result = self.directories[language].output.joinpath(result)

        if track:
            self.generated.add(result)

        return result

    def make_test_path(
        self, name: str, generator: Generator, language: Language
    ) -> Path:
        """Make a path to an interface's unit-test suite."""

        result = self.directories[language].test_dir.joinpath(
            str(generator), f"test_{name}.{language.source_suffix}"
        )
        self.generated.add(result)
        return result

    def rel_include(
        self, name: str, generator: Generator, language: Language
    ) -> Path:
        """Get an include path to a generated output."""

        return (
            self.directories[language]
            .output.relative_to(self.directories[language].source)
            .joinpath(self.make_path(name, generator, language, track=False))
        )

    def get_protocol(self, name: str, exact: bool = False) -> Protocol:
        """Get the protocol instance for a given struct."""

        return self.types.get_protocol(
            name, self.config.data["structs"].get("namespace", []), exact=exact
        )

    def is_struct(self, name: str) -> bool:
        """Determine if a field is a struct or not."""

        try:
            self.get_protocol(type_string(name))
            return True
        except KeyError:
            return False

    def size(
        self, type_name: str, exact: bool = False, trace: bool = False
    ) -> int:
        """Get the size of a given type."""
        return self.types.size(
            type_string(type_name), exact=exact, trace=trace
        )

    def get_enum(self, name: str, exact: bool = False) -> RuntimeEnum:
        """Get a runtime enum instance for a given enumeration."""

        return self.types.get_enum(
            name, *self.config.data["enums"].get("namespace", []), exact=exact
        )

    def is_enum(self, name: str, exact: bool = False) -> bool:
        """Determine if a field is an enumeration or not."""

        try:
            self.get_enum(type_string(name), exact=exact)
            return True
        except KeyError:
            return False
