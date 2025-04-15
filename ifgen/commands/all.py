# =====================================
# generator=datazen
# version=3.2.1
# hash=347b61ef0ea6ed99b2f085b2d17fb232
# =====================================

"""
A module aggregating package commands.
"""

# built-in
from typing import List as _List
from typing import Tuple as _Tuple

# third-party
from vcorelib.args import CommandRegister as _CommandRegister

# internal
from ifgen.commands.gen import add_gen_cmd
from ifgen.commands.svd import add_svd_cmd


def commands() -> _List[_Tuple[str, str, _CommandRegister]]:
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
