"""
An interface for optional code generation plugins.
"""

# internal
from ifgen.enums import Language
from ifgen.generation.interface import GenerateTask
from ifgen.plugins.struct_receiver import (
    cpp_struct_receiver,
    python_struct_receiver,
)

PLUGINS = {
    "struct_receiver": {
        Language.PYTHON: python_struct_receiver,
        Language.CPP: cpp_struct_receiver,
    }
}


def internal_plugin_entry(task: GenerateTask) -> None:
    """A generator for a struct receiver interface."""

    if task.name in PLUGINS and task.language in PLUGINS[task.name]:
        PLUGINS[task.name][task.language](task)
