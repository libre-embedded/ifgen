"""
A module implementing a data model for ARM CMSIS-SVD 'peripheral' data.
"""

# built-in
from dataclasses import dataclass
from typing import Iterable, Optional, Union
from xml.etree import ElementTree

# internal
from ifgen.svd.model.address_block import AddressBlock
from ifgen.svd.model.derived import DerivedMixin
from ifgen.svd.model.device import ARRAY_PROPERTIES, REGISTER_PROPERTIES
from ifgen.svd.model.field import FieldMap
from ifgen.svd.model.interrupt import Interrupt
from ifgen.svd.string import StringKeyVal

RegisterData = list[Union["Register", "Cluster"]]


@dataclass
class Cluster(DerivedMixin):
    """A container for cluster information."""

    derived_from: Optional["Cluster"]
    children: RegisterData
    peripheral: "Peripheral"

    def __eq__(self, other) -> bool:
        """Determine if two clusers are equivalent."""

        return isinstance(other, Cluster) and all(
            x == y for x, y in zip(self.children, other.children)
        )

    @classmethod
    def string_keys(cls) -> Iterable[StringKeyVal]:
        """Get string keys for this instance type."""

        return (
            ARRAY_PROPERTIES
            + [
                StringKeyVal("name", True),
                StringKeyVal("description", False),
                StringKeyVal("alternateCluster", False),
                StringKeyVal("headerStructName", False),
                StringKeyVal("addressOffset", True),
            ]
            + REGISTER_PROPERTIES
        )


def fields_equal(left: Optional[FieldMap], right: Optional[FieldMap]) -> bool:
    """Determine if two field maps are equivalent."""

    result = left is None and right is None

    if left is not None and right is not None and len(left) == len(right):
        for lkey, lvalue in left.items():
            result = lkey in right and lvalue == right[lkey]
            if not result:
                break

    return result


@dataclass
class Register(DerivedMixin):
    """A container for register information."""

    derived_from: Optional["Register"]
    fields: Optional[FieldMap]
    peripheral: "Peripheral"

    def __eq__(self, other) -> bool:
        """Determine if two registers are equivalent."""

        return isinstance(other, Register) and fields_equal(
            self.fields, other.fields
        )

    @property
    def bits(self) -> int:
        """Get the size of this register in bits."""
        result = self.raw_data.get("size", self.peripheral.bits)
        assert result is not None
        return int(result)

    @property
    def size(self) -> int:
        """Get the size of this register in bytes."""
        return self.bits // 8

    @property
    def alternate_group(self) -> Optional[str]:
        """Get this register's possible alternate group."""
        return self.raw_data.get("alternateGroup")

    @property
    def access(self) -> str:
        """Get the access setting for this register."""

        access = self.raw_data.get("access", self.peripheral.access)

        read = False
        write = False

        if access is None and self.fields is not None:
            for field in self.fields.values():
                if "access" in field.raw_data:
                    read |= "read" in field.raw_data["access"]
                    write |= "write" in field.raw_data["access"]

        if read and not write:
            return "read-only"
        if write and not read:
            return "write-only"
        return "read-write"

    @property
    def c_type(self) -> str:
        """Get the C type for this register."""
        return f"uint{self.bits}_t"

    @classmethod
    def string_keys(cls) -> Iterable[StringKeyVal]:
        """Get string keys for this instance type."""

        return (
            ARRAY_PROPERTIES
            + [
                StringKeyVal("name", True),
                StringKeyVal("displayName", False),
                StringKeyVal("description", False),
                StringKeyVal("alternateGroup", False),
                StringKeyVal("alternateRegister", False),
                StringKeyVal("addressOffset", True),
            ]
            + REGISTER_PROPERTIES
            + [
                # is enum
                StringKeyVal("dataType", False),
                # is enum
                StringKeyVal("modifiedWriteValues", False),
                # is enum
                StringKeyVal("readAction", False),
            ]
        )


def register_groups(registers: RegisterData) -> dict[str, list[Register]]:
    """Get groups of registers."""

    result: dict[str, list[Register]] = {}

    for item in registers:
        if isinstance(item, Register):
            alt = item.alternate_group
            if alt:
                if alt not in result:
                    result[alt] = []
                result[alt].append(item)

    return result


@dataclass
class Peripheral(DerivedMixin):
    """A container for peripheral information."""

    derived_from: Optional["Peripheral"]

    # Currently treated as metadata.
    interrupts: list[Interrupt]
    address_blocks: list[AddressBlock]

    registers: RegisterData

    def register_groups(self) -> dict[str, list[Register]]:
        """Get register groups."""
        return register_groups(self.registers)

    def __eq__(self, other) -> bool:
        """Determine if two peripherals are equivalent."""

        return isinstance(other, Peripheral) and all(
            x == y for x, y in zip(self.registers, other.registers)
        )

    @property
    def bits(self) -> Optional[int]:
        """Get size for this peripheral in bits."""

        result = self.derived_elem.raw_data.get("size")
        return int(result) if result is not None else None

    @property
    def access(self) -> Optional[str]:
        """Get the possible 'access' field default."""
        return self.derived_elem.raw_data.get("access")

    def base_name(self, lower: bool = True) -> str:
        """Get the base peripheral name."""

        result = self.name
        result = result.lower() if lower else result
        return result

    def handle_address_block(self, address_block: ElementTree.Element) -> None:
        """Handle an 'address_block' element."""
        self.address_blocks.append(AddressBlock.create(address_block))

    def handle_interrupt(self, interrupt: ElementTree.Element) -> None:
        """Handle an 'interrupt' element."""
        self.interrupts.append(Interrupt.create(interrupt))

    @classmethod
    def string_keys(cls) -> Iterable[StringKeyVal]:
        """Get string keys for this instance type."""

        return (
            ARRAY_PROPERTIES
            + [
                StringKeyVal("name", True),
                StringKeyVal("version", False),
                StringKeyVal("description", False),
                StringKeyVal("alternatePeripheral", False),
                StringKeyVal("groupName", False),
                StringKeyVal("prependToName", False),
                StringKeyVal("appendToName", False),
                StringKeyVal("headerStructName", False),
                StringKeyVal("disableCondition", False),
                StringKeyVal("baseAddress", True),
            ]
            + REGISTER_PROPERTIES
        )
