"""
A module for generating configuration data for struct fields.
"""

# built-in
from typing import Any, Iterable, Optional

# internal
from ifgen.svd.group.enums import ENUM_DEFAULTS, get_enum_name, translate_enums
from ifgen.svd.model.peripheral import (
    Cluster,
    Register,
    RegisterData,
    register_groups,
)

StructMap = dict[str, Any]
StructField = dict[str, Any]


def parse_offset(data: dict[str, str]) -> int:
    """Parse a hex string to get decimal address offset."""

    return int(data["addressOffset"], 16)


def check_not_handled_fields(
    data: dict[str, Any], fields: Iterable[str]
) -> None:
    """Ensure that some keys aren't present in data."""

    for field in fields:
        assert (
            field not in data
        ), f"Field '{field}' isn't currently handled: {data}."


EnumMap = dict[str, Any]


def handle_cluster(
    cluster: Cluster,
    structs: StructMap,
    enums: EnumMap,
    peripheral: str,
    min_enum_members: int,
) -> tuple[int, StructField]:
    """Handle a cluster element."""

    # Ensure that a correct result will be produced.
    check_not_handled_fields(cluster.raw_data, ["alernateCluster"])

    # Register a struct for this cluster. Should we use a namespace for this?
    cluster_struct: dict[str, Any] = cluster.handle_description()
    size, cluster_struct["fields"] = struct_fields(
        cluster.children, structs, enums, peripheral, min_enum_members
    )

    # Too difficult due to padding (may need to comment out). Padding within
    # a cluster isn't currently handled.
    # cluster_struct["expected_size"] = size

    raw_name = sanitize_name(cluster.name)

    cluster_name = cluster.raw_data.get(
        "headerStructName", f"{raw_name}_instance"
    )
    structs[cluster_name] = cluster_struct

    # This needs to be an array element somehow. Use a namespace?
    # dimIncrement not handled.
    array_dim = int(cluster.raw_data.get("dim", 1))

    size *= array_dim
    result: StructField = {
        "name": raw_name,
        "type": cluster_name,
        # Too difficult due to padding (may need to comment out).
        # "expected_size": size,
        # "expected_offset": parse_offset(cluster.raw_data),
    }
    if array_dim > 1:
        result["array_length"] = array_dim

    cluster.handle_description(result)
    return size, result


RegisterMap = dict[str, Register]


def process_bit_fields(
    register: Register,
    output: dict[str, Any],
    enums: EnumMap,
    peripheral: str,
    min_enum_width: int,
) -> None:
    """Get bit-field declarations for a given register."""

    if register.fields is None:
        return

    result: list[dict[str, Any]] = []

    # Process fields.
    for name, field in register.fields.items():
        field_data: dict[str, Any] = {"name": name}
        field_data.update(field.ifgen_data)
        result.append(field_data)

        # Handle creating an enumeration.
        if field.enum is not None:
            # Register enumeration.
            raw = translate_enums(field.enum)

            if field_data["width"] >= min_enum_width:
                new_enum: dict[str, Any] = {"enum": raw}
                new_enum.update(ENUM_DEFAULTS)

                # Increase size of underlying if necessary.
                if field_data["width"] > 8:
                    new_enum["underlying"] = "uint16_t"

                # Check if enum is unique.
                enum_name = get_enum_name(
                    sanitize_name(f"{peripheral}_{register.name}_{name}"),
                    peripheral,
                    raw,
                )
                field_data["type"] = enum_name
                if enum_name not in enums:
                    enums[enum_name] = new_enum

    if result:
        output["fields"] = result


def sanitize_name(name: str) -> str:
    """Remove special characters from a name."""

    return name.replace("[%s]", "").replace("%s", "")


def handle_register(
    register: Register,
    register_map: RegisterMap,
    enums: EnumMap,
    peripheral: str,
    min_enum_width: int,
) -> tuple[int, StructField]:
    """Handle a register entry."""

    # Handle adding a union entry to the main field and handle this register's
    # bit fields.
    if "alternateRegister" in register.raw_data:
        return 0, {}

    # Currently provided in metadata output.
    # check_not_handled_fields(register.raw_data, ["alternateGroup"])

    # dimIncrement not handled.
    array_dim = int(register.raw_data.get("dim", 1))

    size = register.size * array_dim
    data = {
        "name": sanitize_name(register.name),
        "type": register.c_type,
        "expected_size": size,
        "expected_offset": parse_offset(register.raw_data),
    }
    if array_dim > 1:
        data["array_length"] = array_dim

    access = register.access
    if access == "read-only":
        data["const"] = True

    notes = [access]

    register.handle_description(data, prefix=f"({', '.join(notes)}) ")

    # Handle bit fields.
    process_bit_fields(register, data, enums, peripheral, min_enum_width)

    # Handle alternates.
    alts = register.alternates
    if alts:
        alts_data: list[dict[str, Any]] = []

        for item in alts:
            alt_data: dict[str, Any] = {"name": item.name}
            if item.access == "read-only":
                alt_data["const"] = True
            item.handle_description(alt_data, prefix=f"({item.access}) ")

            process_bit_fields(
                register_map[item.name],
                alt_data,
                enums,
                peripheral,
                min_enum_width,
            )

            # Forward array information (might be necessary at some point).
            # if "array_length" in data:
            #     alt_data["array_length"] = data["array_length"]

            alts_data.append(alt_data)

        data["alternates"] = alts_data

    return size, data


def handle_register_group(
    name: str,
    registers: list[Register],
    register_map: RegisterMap,
    enums: EnumMap,
    peripheral: str,
    min_enum_width: int,
) -> tuple[int, StructField]:
    """Handle creating a struct field for a group of registers."""

    # Handle melding register data at some point (aggregate more bit fields).
    del name

    return handle_register(
        registers[0], register_map, enums, peripheral, min_enum_width
    )


def handle_item(
    item: Register | Cluster,
    structs: StructMap,
    enums: EnumMap,
    peripheral: str,
    min_enum_width: int,
    groups_handled: set[str],
    register_map: RegisterMap,
    groups: dict[str, list[Register]],
    by_name: dict[str, str],
) -> tuple[int, Optional[StructField]]:
    """Handle creating a struct field from a register or cluster."""

    inst_size = 0
    field = None

    if isinstance(item, Cluster):
        inst_size, field = handle_cluster(
            item, structs, enums, peripheral, min_enum_width
        )
    else:
        # Handle register groups.
        if item.name in by_name:
            group = by_name[item.name]
            if group not in groups_handled:
                inst_size, field = handle_register_group(
                    group,
                    groups[group],
                    register_map,
                    enums,
                    peripheral,
                    min_enum_width,
                )
                groups_handled.add(group)

        # Handle normal registers.
        else:
            inst_size, field = handle_register(
                item, register_map, enums, peripheral, min_enum_width
            )

    return inst_size, field


def struct_fields(
    registers: RegisterData,
    structs: StructMap,
    enums: EnumMap,
    peripheral: str,
    min_enum_width: int,
    size: int = None,
) -> tuple[int, list[StructField]]:
    """Generate data for struct fields."""

    fields = []

    if size is None:
        size = 0

    # Create a string mapping of registers.
    register_map: RegisterMap = {}
    for item in registers:
        if isinstance(item, Register):
            register_map[item.name] = item

    groups = register_groups(registers)
    by_name = {}
    for group, regs in groups.items():
        for reg in regs:
            by_name[reg.name] = group
    groups_handled: set[str] = set()

    for item in registers:
        inst_size, field = handle_item(
            item,
            structs,
            enums,
            peripheral,
            min_enum_width,
            groups_handled,
            register_map,
            groups,
            by_name,
        )

        if inst_size > 0 and field is not None:
            fields.append(field)
            size += inst_size

    return size, fields
