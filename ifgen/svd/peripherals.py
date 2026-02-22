"""
A module implementing a 'peripherals' SVD-element processor.
"""

# built-in
from xml.etree import ElementTree

# third-party
from vcorelib.logging import LoggerType

# internal
from ifgen.svd.model.derived import derived_from_stack
from ifgen.svd.model.peripheral import Peripheral
from ifgen.svd.process import handle_registers
from ifgen.svd.task import SvdProcessingTask


def process_peripheral(
    elem: ElementTree.Element,
    task: SvdProcessingTask,
    logger: LoggerType,
    system_width_bits: int = 32,
) -> None:
    """Process a SVD peripheral element."""

    derived_periph = None
    derived = elem.attrib.get("derivedFrom")
    if derived is not None:
        derived_periph = task.model.peripherals[derived]

    peripheral = Peripheral.create(
        elem, derived_periph, [], [], [], system_width_bits
    )
    peripheral.log(elem, logger)

    # Handle registers.
    registers = elem.find("registers")
    if registers is not None:
        peripheral.registers = handle_registers(registers, peripheral)

    # Handle address blocks.
    for address_block in elem.iterfind("addressBlock"):
        peripheral.handle_address_block(address_block)

    # Handle interrupts.
    for interrupt in elem.iterfind("interrupt"):
        peripheral.handle_interrupt(interrupt)

    task.model.register_peripheral(elem, peripheral)


def process_peripherals(
    elem: ElementTree.Element, task: SvdProcessingTask, logger: LoggerType
) -> None:
    """Process a SVD peripherals element."""

    del logger

    for item in derived_from_stack(elem.iterfind("peripheral")):
        task.process(item)
