"""
A module implementing interfaces to facilitate code generation.
"""

# built-in
from logging import getLogger
from multiprocessing.pool import ThreadPool
from pathlib import Path
from typing import Dict, List

# internal
from ifgen.common import create_common, create_common_test
from ifgen.config import Config
from ifgen.enum import create_enum, create_enum_source, create_enum_test
from ifgen.environment import Generator, IfgenEnvironment, Language
from ifgen.generation.interface import GenerateTask, InstanceGenerator
from ifgen.struct import (
    create_struct,
    create_struct_test,
)

GENERATORS: Dict[Generator, List[InstanceGenerator]] = {
    Generator.STRUCTS: [create_struct, create_struct_test],
    Generator.ENUMS: [create_enum, create_enum_test, create_enum_source],
    Generator.IFGEN: [create_common, create_common_test],
}
LOG = getLogger(__name__)


def generate(root: Path, config: Config) -> None:
    """Generate struct files."""

    env = IfgenEnvironment(root, config)

    # Search for language configurations.
    languages = [x for x in Language if config.data.get(x.cfg_dir_name)]
    LOG.info("Generating for languages: %s.", languages)

    with ThreadPool() as pool:
        for language in languages:
            for generator, methods in GENERATORS.items():
                for method in methods:
                    pool.map(
                        method,
                        (
                            GenerateTask(
                                name,
                                generator,
                                language,
                                env.make_path(
                                    name,
                                    generator,
                                    language,
                                    from_output=True,
                                ),
                                env.make_test_path(name, generator, language),
                                data,
                                env,
                            )
                            for name, data in config.data.get(
                                generator.value, {}
                            ).items()
                        ),
                    )

    env.prune_empty()
