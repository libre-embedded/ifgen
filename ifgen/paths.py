"""
A module exposing some pathing utilities.
"""

# built-in
from pathlib import Path

# third-party
from vcorelib.paths import Pathlike, normalize


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
