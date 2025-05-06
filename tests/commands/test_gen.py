"""
Test the 'commands.gen' module.
"""

# built-in
from subprocess import run
from sys import executable, platform
from typing import Any

# third-party
from vcorelib.io import ARBITER

# module under test
from ifgen import PKG_NAME
from ifgen.entry import main as ifgen_main

# internal
from tests.resources import clean_scenario


def test_ifgen_command_basic():
    """Test the 'gen' command."""

    path = clean_scenario("sample")
    assert ifgen_main([PKG_NAME, "gen", "-r", str(path)]) == 0

    # Attempt to build and run generated tests.
    if platform == "linux":
        run([executable, "-m", "yambs", "-C", str(path), "native"], check=True)
        run(
            ["ninja", "-C", str(path), "debug", "clang"],
            check=True,
        )

        # Run test apps.
        data: dict[str, Any] = ARBITER.decode(
            path.joinpath("ninja", "apps.json"), require_success=True
        ).data
        tests = data["tests"]
        for name, data in data["all"].items():
            for variant in ["debug", "clang"]:
                if name in tests:
                    run([data["variants"][variant]], check=True)

        run(
            ["ninja", "-C", str(path), "format-check"],
            check=True,
        )
