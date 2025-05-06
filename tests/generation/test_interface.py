"""
Test the 'generation.interface' module.
"""

# internal
from ifgen.paths import create_formatter


def test_clang_format() -> None:
    """Test the interface to clang-format."""

    assert create_formatter("clang-format")(
        """
    int main(void) {return 0;}
    """
    )
