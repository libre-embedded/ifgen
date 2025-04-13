"""
Utility interfaces related to struct code generation.
"""

# internal
from ifgen.generation.interface import GenerateTask


def struct_dependencies(task: GenerateTask) -> set[str]:
    """Generates string type names for dependencies."""

    unique = set()

    for config in task.instance["fields"]:
        if "type" in config:
            unique.add(config["type"])

        # Add includes for bit-fields.
        for bit_field in config.get("fields", []):
            if "type" in bit_field:
                unique.add(bit_field["type"])

        # Add includes for alternates.
        for alternate in config.get("alternates", []):
            for alternate_bit_field in alternate.get("fields", []):
                if "type" in alternate_bit_field:
                    unique.add(alternate_bit_field["type"])

    return unique
