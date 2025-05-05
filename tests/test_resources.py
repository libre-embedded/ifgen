"""
Test that we can load test resources.
"""

# built-in
from pathlib import Path
from tempfile import TemporaryDirectory

# module under test
from ifgen.generation.interface import apply_cpp_namespace
from ifgen.paths import audit_init_file

# internal
from tests.resources import resource


def test_resources_basic():
    """Test that we can locate test data."""

    assert apply_cpp_namespace("test", "test", header=False)

    assert resource("test.txt").is_file()
    assert resource("test.txt", valid=False).is_file()

    with TemporaryDirectory() as tmpdir:
        audit_init_file(Path(tmpdir, "test.py"))
