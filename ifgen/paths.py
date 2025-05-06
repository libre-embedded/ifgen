"""
A module exposing some pathing utilities.
"""

# built-in
from pathlib import Path
import shutil
import subprocess

# third-party
from vcorelib.paths import Pathlike, normalize
from vcorelib.paths.context import TextPreprocessor


def combine_if_not_absolute(root: Path, candidate: Pathlike) -> Path:
    """Combine a root directory with a path if the path isn't absolute."""

    candidate = normalize(candidate)
    return candidate if candidate.is_absolute() else root.joinpath(candidate)


def audit_init_file(source: Path, parent_depth: int = 0) -> None:
    """Create initialization files if necessary."""

    candidate = source.parent.joinpath("__init__.py")
    if not candidate.exists():
        with candidate.open("wb") as stream:
            stream.write(bytes())

    # Audit parent directories.
    if parent_depth > 0:
        parent_depth -= 1
        audit_init_file(source.parent, parent_depth=parent_depth)


def create_formatter(*args: str, **kwargs) -> TextPreprocessor:
    """
    Create a formatting preprocessor that uses stdin/stdout of a subprocess.
    """

    def formatter(data: str) -> str:
        """Run clang-format on the provided data."""

        result = data

        if args and shutil.which(args[0]) is not None:
            result = subprocess.run(
                args,
                input=data,
                text=True,
                capture_output=True,
                check=True,
                **kwargs,
            ).stdout

        return result

    return formatter
