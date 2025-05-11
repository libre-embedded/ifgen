"""
A module implementing enumerations used by this package.
"""

# built-in
from enum import StrEnum

# third-party
from vcorelib.names import to_snake

# internal
from ifgen import PKG_NAME


class Generator(StrEnum):
    """An enumeration declaring all valid kinds of generators."""

    STRUCTS = "structs"
    ENUMS = "enums"
    IFGEN = PKG_NAME
    CUSTOM = "custom"


class Language(StrEnum):
    """An enumeration declaring output generation variants."""

    CPP = "CPP"
    PYTHON = "Python"

    @property
    def source_suffix(self) -> str:
        """Get a source-file suffix for this language."""
        return "cc" if self is Language.CPP else "py"

    @property
    def header_suffix(self) -> str:
        """Get a header-file suffix for this language."""
        return "h" if self is Language.CPP else "py"

    @property
    def slug(self) -> str:
        """Get a slug string."""
        return to_snake(self.name)

    @property
    def cfg_dir_name(self) -> str:
        """
        Get the configuration key for this language's output configuration.
        """
        return f"{self.slug}_dir"
