# -*- coding: utf-8 -*-

"""This module contains the message class for the simulation platform resource state messages."""

from __future__ import annotations
from typing import Any, Dict, Union

from tools.exceptions.messages import MessageValueError
from tools.message.abstract import AbstractResultMessage, AbstractMessage
from tools.message.block import QuantityBlock
from tools.tools import FullLogger

LOGGER = FullLogger(__name__)


class ResourceStateMessage(AbstractResultMessage):
    """Class containing all the attributes for a ResourceState message."""

    # message type for these messages
    CLASS_MESSAGE_TYPE = "ResourceState"
    MESSAGE_TYPE_CHECK = True

    # Mapping from message JSON attributes to class attributes
    MESSAGE_ATTRIBUTES = {
        "Bus": "bus",
        "RealPower": "real_power",
        "ReactivePower": "reactive_power",
        "Node": "node"
    }
    OPTIONAL_ATTRIBUTES = ["Node"]

    # attributes whose value should be a QuantityBlock and the expected unit of measure.
    QUANTITY_BLOCK_ATTRIBUTES = {
        "RealPower": "kW",
        "ReactivePower": "kV.A{r}"
    }

    MESSAGE_ATTRIBUTES_FULL = {
        **AbstractResultMessage.MESSAGE_ATTRIBUTES_FULL,
        **MESSAGE_ATTRIBUTES
    }
    OPTIONAL_ATTRIBUTES_FULL = AbstractResultMessage.OPTIONAL_ATTRIBUTES_FULL + OPTIONAL_ATTRIBUTES
    QUANTITY_BLOCK_ATTRIBUTES_FULL = {
        **AbstractMessage.QUANTITY_BLOCK_ATTRIBUTES_FULL,
        **QUANTITY_BLOCK_ATTRIBUTES
    }

    # allowed values for the node attribute
    ACCEPTED_NODE_VALUES = [1, 2, 3]

    @property
    def bus(self) -> str:
        """The attribute for the name of bus to which the resource is connected."""
        return self.__bus

    @property
    def real_power(self) -> QuantityBlock:
        """The attribute for real power of the resource."""
        return self.__real_power

    @property
    def reactive_power(self) -> QuantityBlock:
        """The attribute for reactive power of the resource."""
        return self.__reactive_power

    @property
    def node(self) -> Union[int, None]:
        """Node that 1-phase resource is connected to.
           If this is not specified then it is assumed that the resource is 3-phase resource."""
        return self.__node

    @bus.setter
    def bus(self, bus: str):
        """Set value for bus."""
        if self._check_bus(bus):
            self.__bus = bus
            return

        raise MessageValueError(f"'{bus}' is an invalid value for bus since it is not a string.")

    @real_power.setter
    def real_power(self, real_power: Union[str, float, QuantityBlock, Dict[str, Any]]):
        """Set value for real power.
        A string value is converted to a float. A float value is converted into a QuantityBlock with the default unit.
        Raises MessageValueError if value is missing or invalid: a QuantityBlock has the wrong unit or
        a string cannot be converted to float"""
        unit = self.QUANTITY_BLOCK_ATTRIBUTES['RealPower']
        if self._check_power(real_power, unit):
            if isinstance(real_power, QuantityBlock):
                self.__real_power = real_power

            elif isinstance(real_power, dict):
                self.__real_power = QuantityBlock(**real_power)

            else:
                self.__real_power = QuantityBlock(Value=float(real_power), UnitOfMeasure=unit)

            return

        raise MessageValueError("'{:s}' is an invalid value for real power.".format(str(real_power)))

    @reactive_power.setter
    def reactive_power(self, reactive_power: Union[str, float, QuantityBlock, Dict[str, Any]]):
        """Set value for reactive power.
        A string value is converted to a float. A float value is converted into a QuantityBlock with the default unit.
        Raises MessageValueError if value is missing or invalid: a QuantityBlock has the wrong unit or
        a string cannot be converted to float"""
        unit = self.QUANTITY_BLOCK_ATTRIBUTES['ReactivePower']
        if self._check_power(reactive_power, unit):
            if isinstance(reactive_power, QuantityBlock):
                self.__reactive_power = reactive_power

            elif isinstance(reactive_power, dict):
                self.__reactive_power = QuantityBlock(**reactive_power)

            else:
                self.__reactive_power = QuantityBlock(Value=float(reactive_power), UnitOfMeasure=unit)
            return

        raise MessageValueError("'{:s}' is an invalid value for reactive power.".format(str(reactive_power)))

    @node.setter
    def node(self, node: Union[int, None]):
        """Set value for node."""
        if self._check_node(node):
            if node is not None:
                self.__node = int(node)

            else:
                self.__node = node

            return

        raise MessageValueError(f"'{node}' is an invalid value for node: not an integer 1, 2 or 3.")

    def __eq__(self, other: Any) -> bool:
        """Check that two ResourceStateMessages represent the same message."""
        return (
            super().__eq__(other) and
            isinstance(other, ResourceStateMessage) and
            self.bus == other.bus and
            self.real_power == other.real_power and
            self.reactive_power == other.reactive_power and
            self.node == other.node
        )

    @classmethod
    def _check_bus(cls, bus: str) -> bool:
        """Check that value for bus is valid i.e. a string."""
        return isinstance(bus, str)

    @classmethod
    def _check_power(cls, power: Union[str, float, QuantityBlock, dict], unit: str) -> bool:
        """Check that value for real or reactive power is valid.
        String can be converted to float or the given QuantityBlock has the given unit."""
        if isinstance(power, (QuantityBlock, dict)):
            if isinstance(power, dict):
                if not QuantityBlock.validate_json(power):
                    return False
                power = QuantityBlock(**power)

            return power.unit_of_measure == unit

        try:
            float(power)
            return True

        except (ValueError, TypeError):
            return False

    @classmethod
    def _check_real_power(cls, real_power: Union[str, float, QuantityBlock]) -> bool:
        """Check that value for real power is valid."""
        return cls._check_power(real_power, cls.QUANTITY_BLOCK_ATTRIBUTES['RealPower'])

    @classmethod
    def _check_reactive_power(cls, reactive_power: Union[str, float, QuantityBlock]) -> bool:
        """Check that value for reactive power is valid."""
        return cls._check_power(reactive_power, cls.QUANTITY_BLOCK_ATTRIBUTES['ReactivePower'])

    @classmethod
    def _check_node(cls, node: Union[int, None]) -> bool:
        """Check that node is None or something that can be converted to integer and its value is 1, 2 or 3."""
        if node is None:
            return True

        try:
            node = int(node)
            return node in cls.ACCEPTED_NODE_VALUES

        except ValueError:
            return False

    @classmethod
    def from_json(cls, json_message: Dict[str, Any]) -> Union[ResourceStateMessage, None]:
        """Returns a class object created based on the given JSON attributes.
           If the given JSON is not validated returns None."""
        if cls.validate_json(json_message):
            return cls(**json_message)
        return None
