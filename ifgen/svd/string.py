"""
A module implementing interfaces for string-data elements.
"""

# built-in
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Iterable, Optional, Type, TypeVar
from xml.etree import ElementTree

# third-party
from ruamel.yaml.scalarstring import LiteralScalarString
from vcorelib.logging import LoggerType


@dataclass
class StringKeyVal:
    """Name of key and whether or not it's required."""

    key: str
    required: bool = True


T = TypeVar("T", bound="StringKeyValueMixin")


class StringKeyValueMixin(ABC):
    """A mixin for SVD data model classes."""

    raw_data: dict[str, str]

    @classmethod
    def create(cls: Type[T], elem: ElementTree.Element, *args, **kwargs) -> T:
        """Create a device instance from an element."""

        inst = cls(*args, **kwargs)
        inst.raw(elem)
        return inst

    @classmethod
    @abstractmethod
    def string_keys(cls) -> Iterable[StringKeyVal]:
        """Get string keys for this instance type."""

    def handle_description(
        self, data: dict[str, Any] = None, prefix: str = None
    ) -> dict[str, Any]:
        """Handle a possible description entry."""

        if data is None:
            data = {}

        description = self.raw_data.get("description")

        if description:
            data["description"] = LiteralScalarString(
                (prefix if prefix else "") + description
            ).replace("\\n", "")

        return data

    def raw(self, elem: ElementTree.Element) -> dict[str, str]:
        """Get raw data for this instance based on string keys."""

        result = getattr(self, "raw_data", None)
        if result is None:
            self.raw_data = self.get_values(elem)
            result = self.raw_data

        assert result is not None
        return result

    def log(
        self, elem: ElementTree.Element, logger: Optional[LoggerType]
    ) -> None:
        """Log information from this instance's raw data."""

        if logger is not None:
            for key, value in self.raw(elem).items():
                for line in value.splitlines():
                    line = line.strip().replace("\\n", "")
                    if line:
                        logger.info("%s: %s", key, line)

    @classmethod
    def get_values(cls, elem: ElementTree.Element) -> dict[str, str]:
        """Get string values for this instance."""

        return get_string_values(elem, cls.string_keys())


def get_string_values(
    elem: ElementTree.Element, keys: Iterable[StringKeyVal]
) -> dict[str, str]:
    """Get string values from an element's children."""

    result = {}

    for item in keys:
        key = item.key
        required = item.required

        new_elem = elem.find(key)
        assert (
            new_elem is not None or not required
        ), f"'{key}' required but not found!"
        if new_elem is not None:
            result[key] = new_elem.text or ""

    return result
