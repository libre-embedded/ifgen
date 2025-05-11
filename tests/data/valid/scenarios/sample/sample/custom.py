"""
A module implementing a custom code generator.
"""

# third-party
from ifgen.generation.interface import GenerateTask


def test1(task: GenerateTask) -> None:
    """Sample generator."""

    if "a" in task.instance:
        print(f"(test1) {task.name} {task.instance}")
        assert task.instance == {"a": 1, "b": 2, "c": 3}


def test2(task: GenerateTask) -> None:
    """Sample generator."""

    if "a" in task.instance:
        print(f"(test2) {task.name} {task.instance}")
        assert task.instance == {"a": 1, "b": 2, "c": 3}
