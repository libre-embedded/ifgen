"""
A module implementing an SVD-processing task interface.
"""

# built-in
from dataclasses import dataclass
from logging import getLogger
from pathlib import Path
from typing import Callable, Iterable, Iterator
from xml.etree import ElementTree

# third-party
from vcorelib.io import ARBITER
from vcorelib.logging import LoggerType
from vcorelib.paths import rel

# internal
from ifgen.config.svd import SvdConfig
from ifgen.svd.group import handle_group, peripheral_groups
from ifgen.svd.model import SvdModel

TagProcessor = Callable[
    [ElementTree.Element, "SvdProcessingTask", LoggerType], None
]
TagProcessorMap = dict[str, TagProcessor]
TAG_PROCESSORS: TagProcessorMap = {}


def filter_includes(
    config: SvdConfig,
    model: SvdModel,
    paths: Iterable[Path],
    filtered: dict[str, str],
) -> Iterator[str]:
    """Filter includes based on configuration."""

    config_data = config.data.setdefault("devices", {}).setdefault(
        model.device_name.lower(), {"ignore_peripherals": []}
    )

    for path in paths:
        item = str(path)
        reason = None

        # Determine a possible reason to filter this include.
        for ignore in config_data["ignore_peripherals"]:
            if path.parts[0] == ignore["name"]:
                reason = ignore["reason"]

        if reason is not None:
            filtered[item] = reason
        else:
            yield item


@dataclass
class SvdProcessingTask:
    """A container for SVD-processing state."""

    model: SvdModel
    min_enum_width: int

    def process(self, elem: ElementTree.Element) -> None:
        """Process a single element."""
        TAG_PROCESSORS[elem.tag](elem, self, getLogger(elem.tag))

    @staticmethod
    def svd(path: Path, min_enum_width: int) -> "SvdProcessingTask":
        """Process a single SVD file."""

        task = SvdProcessingTask(SvdModel({}), min_enum_width)
        task.process(ElementTree.parse(path).getroot())
        return task

    def generate_configs(self, path: Path, config: SvdConfig) -> None:
        """Generate output configuration files."""

        path.mkdir(exist_ok=True, parents=True)

        includes: set[Path] = set()

        # Organize peripherals into groups based on ones derived from others
        # and process them.
        for group in peripheral_groups(self.model.peripherals).values():
            output_dir = path.joinpath(group.root.base_name())
            output_dir.mkdir(exist_ok=True)
            handle_group(output_dir, group, includes, self.min_enum_width)

        # Write metadata that doesn't currently get used for generation.
        meta = self.model.metadata()

        # Indicate includes that were filtered out in metadata.
        filtered: dict[str, str] = {}
        meta["filtered_includes"] = filtered

        ARBITER.encode(
            path.joinpath("ifgen.yaml"),
            {
                "includes": sorted(  # type: ignore
                    filter_includes(
                        config,
                        self.model,
                        (rel(x.resolve(), base=path) for x in includes),
                        filtered,
                    )
                ),
                "namespace": self.model.namespace(),  # type: ignore
                "struct": {
                    "stream": False,
                    "codec": False,
                    "methods": False,
                    "unit_test": False,
                },
                "enum": {"use_map": False, "identifier": False},
            },
        )
        ARBITER.encode(path.joinpath("metadata.json"), meta)
