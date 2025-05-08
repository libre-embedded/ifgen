# =====================================
# generator=datazen
# version=3.2.3
# hash=59dca672992f53400ea71bca41a0a863
# =====================================

"""
A module aggregating package commands.
"""

# third-party
from vcorelib.args import CommandRegister as _CommandRegister

# internal
from ifgen.commands.gen import add_gen_cmd
from ifgen.commands.svd import add_svd_cmd


def commands() -> list[tuple[str, str, _CommandRegister]]:
    """Get this package's commands."""

    return [
        (
            "gen",
            "generate interfaces",
            add_gen_cmd,
        ),
        (
            "svd",
            "process CMSIS-SVD files",
            add_svd_cmd,
        ),
        ("noop", "command stub (does nothing)", lambda _: lambda _: 0),
    ]
