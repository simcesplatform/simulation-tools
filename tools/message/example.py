# -*- coding: utf-8 -*-

"""This module contains the message class for a example message."""

from __future__ import annotations
from typing import Any, Dict, Union

from tools.exceptions.messages import MessageValueError
from tools.message.abstract import AbstractResultMessage
from tools.message.block import QuantityBlock, TimeSeriesBlock
from tools.tools import FullLogger

LOGGER = FullLogger(__name__)


class ExampleMessage(AbstractResultMessage):
    """Example message class that for testing and demonstration purposes."""

    CLASS_MESSAGE_TYPE = "Example"
    MESSAGE_TYPE_CHECK = True

    # required: only positive integers (> 0) allowed
    INTEGER_ATTRIBUTE = "PositiveInteger"
    # required: QuantityBlock with the values given in watts
    POWER_ATTRIBUTE = "PowerQuantity"
    # required: TimeSeriesBlock with exactly two series: "PlaceA" and "PlaceB" with the values given in both series
    # in Celsius and there being at least 3 values in each series
    TEMPERATURE_ATTRIBUTE = "Temperature"
    TEMPERATURE_SERIES_NAMES = ["PlaceA", "PlaceB"]
    TEMPERATURE_SERIES_UNIT = "Cel"

    # optional: must be exactly 8 characters
    CHARACTER_ATTRIBUTE = "EightCharacters"
    # optional: QuantityBlock with the value given in seconds and value fulfilling the equation 0 <= value <= 86400
    TIME_ATTRIBUTE = "TimeQuantity"
    # optional: TimeSeriesBlock with at least one series (no restrictions on the series name) and the the values given
    # either in grams or in kilograms.
    WEIGHT_ATTRIBUTE = "Weight"
    ALLOWED_WEIGHT_UNITS = ["g", "kg"]

    # all attributes specific that are added to the AbstractResult should be introduced here
    MESSAGE_ATTRIBUTES = {
        INTEGER_ATTRIBUTE: "positive_integer",
        POWER_ATTRIBUTE: "power_quantity",
        TEMPERATURE_ATTRIBUTE: "temperature",
        CHARACTER_ATTRIBUTE: "eight_characters",
        TIME_ATTRIBUTE: "time_quantity",
        WEIGHT_ATTRIBUTE: "weight"
    }
    # list all attributes that are optional here (use the JSON attribute names)
    OPTIONAL_ATTRIBUTES = [
        CHARACTER_ATTRIBUTE,
        TIME_ATTRIBUTE,
        WEIGHT_ATTRIBUTE
    ]

    # all attributes that are using the Quantity block format should be listed here
    QUANTITY_BLOCK_ATTRIBUTES = {
        POWER_ATTRIBUTE: "W",
        TIME_ATTRIBUTE: "s"
    }

    # all attributes that are using the Time series block format should be listed here
    TIMESERIES_BLOCK_ATTRIBUTES = [
        TEMPERATURE_ATTRIBUTE,
        WEIGHT_ATTRIBUTE
    ]

    # always include these definitions to update the full list of attributes to these class variables
    MESSAGE_ATTRIBUTES_FULL = {
        **AbstractResultMessage.MESSAGE_ATTRIBUTES_FULL,
        **MESSAGE_ATTRIBUTES
    }
    OPTIONAL_ATTRIBUTES_FULL = AbstractResultMessage.OPTIONAL_ATTRIBUTES_FULL + OPTIONAL_ATTRIBUTES
    QUANTITY_BLOCK_ATTRIBUTES_FULL = {
        **AbstractResultMessage.QUANTITY_BLOCK_ATTRIBUTES_FULL,
        **QUANTITY_BLOCK_ATTRIBUTES
    }
    TIMESERIES_BLOCK_ATTRIBUTES_FULL = (
        AbstractResultMessage.TIMESERIES_BLOCK_ATTRIBUTES_FULL +
        TIMESERIES_BLOCK_ATTRIBUTES
    )

    # for each attributes added by this message type provide a property function to get the value of the attribute
    # the name of the properties must correspond to the names given in MESSAGE_ATTRIBUTES
    @property
    def positive_integer(self) -> int:
        """The value of the PositiveInteger attribute."""
        return self.__positive_integer

    @property
    def power_quantity(self) -> QuantityBlock:
        """The value of the PowerQuantity attribute."""
        return self.__power_quantity  # type: ignore  # pylint: disable=no-member

    @property
    def temperature(self) -> TimeSeriesBlock:
        """The value of the Temperature attribute."""
        return self.__temperature  # type: ignore  # pylint: disable=no-member

    @property
    def eight_characters(self) -> Union[str, None]:
        """The value of the EightCharacters attribute."""
        return self.__eight_characters

    @property
    def time_quantity(self) -> Union[QuantityBlock, None]:
        """The value of the TimeQuantity attribute."""
        return self.__time_quantity  # type: ignore  # pylint: disable=no-member

    @property
    def weight(self) -> Union[TimeSeriesBlock, None]:
        """The value of the Weight attribute."""
        return self.__weight  # type: ignore  # pylint: disable=no-member

    # for each attributes added by this message type provide a property setter function to set the value of
    # the attribute the name of the properties must correspond to the names given in MESSAGE_ATTRIBUTES
    @positive_integer.setter
    def positive_integer(self, positive_integer: int):
        if self._check_positive_integer(positive_integer):
            self.__positive_integer = positive_integer
        else:
            raise MessageValueError("Invalid value, {}, for attribute: positive_integer".format(positive_integer))

    @power_quantity.setter
    def power_quantity(self, power_quantity: Union[str, float, QuantityBlock, Dict[str, Any]]):
        if self._check_power_quantity(power_quantity):
            self._set_quantity_block_value(self.POWER_ATTRIBUTE, power_quantity)
        else:
            raise MessageValueError("Invalid value, {}, for attribute: power_quantity".format(power_quantity))

    @temperature.setter
    def temperature(self, temperature: Union[TimeSeriesBlock, Dict[str, Any]]):
        if self._check_temperature(temperature):
            self._set_timeseries_block_value(self.TIME_ATTRIBUTE, temperature)
        else:
            raise MessageValueError("Invalid value, {}, for attribute: temperature".format(temperature))

    @eight_characters.setter
    def eight_characters(self, eight_characters: Union[str, None]):
        if self._check_eight_characters(eight_characters):
            self.__eight_characters = eight_characters
        else:
            raise MessageValueError("Invalid value, {}, for attribute: eight_characters".format(eight_characters))

    @time_quantity.setter
    def time_quantity(self, time_quantity: Union[str, float, QuantityBlock, Dict[str, Any], None]):
        if self._check_time_quantity(time_quantity):
            self._set_quantity_block_value(self.TIME_ATTRIBUTE, time_quantity)
        else:
            raise MessageValueError("Invalid value, {}, for attribute: time_quantity".format(time_quantity))

    @weight.setter
    def weight(self, weight: Union[TimeSeriesBlock, Dict[str, Any], None]):
        if self._check_weight(weight):
            self._set_timeseries_block_value(self.WEIGHT_ATTRIBUTE, weight)
        raise MessageValueError("Invalid value, {}, for attribute: weight".format(weight))

    # provide a new implementation for the "test of message equality" function
    def __eq__(self, other: Any) -> bool:
        return (
            super().__eq__(other) and
            isinstance(other, ExampleMessage) and
            self.positive_integer == other.positive_integer and
            self.power_quantity == other.power_quantity and
            self.temperature == other.temperature and
            self.eight_characters == other.eight_characters and
            self.time_quantity == other.time_quantity and
            self.weight == other.weight
        )

    # Provide a class method for each attribute added by this message type to check if the value is acceptable
    # These should return True only when the given parameter corresponds to an acceptable value for the attribute
    @classmethod
    def _check_positive_integer(cls, positive_integer: int) -> bool:
        return positive_integer > 0

    @classmethod
    def _check_power_quantity(cls, power_quantity: Union[str, float, QuantityBlock, Dict[str, Any]]) -> bool:
        return cls._check_quantity_block(
            value=power_quantity,
            unit=cls.QUANTITY_BLOCK_ATTRIBUTES[cls.POWER_ATTRIBUTE]
        )

    @classmethod
    def _check_temperature(cls, temperature: Union[TimeSeriesBlock, Dict[str, Any]]) -> bool:
        return cls._check_timeseries_block(
            value=temperature,
            block_check=cls._check_temperature_block
        )

    @classmethod
    def _check_eight_characters(cls, eight_characters: Union[str, None]) -> bool:
        return eight_characters is None or len(eight_characters) == 8

    @classmethod
    def _check_time_quantity(cls, time_quantity: Union[str, float, QuantityBlock, Dict[str, Any], None]) -> bool:
        return cls._check_quantity_block(
            value=time_quantity,
            unit=cls.QUANTITY_BLOCK_ATTRIBUTES[cls.TIME_ATTRIBUTE],
            can_be_none=True,
            float_value_check=lambda value: 0.0 <= value <= 86400.0
        )

    @classmethod
    def _check_weight(cls, weight: Union[TimeSeriesBlock, Dict[str, Any], None]) -> bool:
        return cls._check_timeseries_block(
            value=weight,
            can_be_none=True,
            block_check=cls._check_weight_block
        )

    @classmethod
    def _check_temperature_block(cls, temperature_block: TimeSeriesBlock) -> bool:
        block_series = temperature_block.series
        if len(block_series) != 2 or len(temperature_block.time_index) < 3:
            return False

        for temperature_series_name in cls.TEMPERATURE_SERIES_NAMES:
            if temperature_series_name not in block_series:
                return False
            current_series = block_series[temperature_series_name]
            if current_series.unit_of_measurement != cls.TEMPERATURE_SERIES_UNIT or len(current_series.values) < 3:
                return False

        return True

    @classmethod
    def _check_weight_block(cls, weight_block: TimeSeriesBlock) -> bool:
        block_series = weight_block.series
        if len(block_series) < 1:
            return False

        for _, series_attribute in block_series.items():
            if series_attribute.unit_of_measurement not in cls.ALLOWED_WEIGHT_UNITS:
                return False

        return True

    @classmethod
    def from_json(cls, json_message: Dict[str, Any]) -> Union[ExampleMessage, None]:
        if cls.validate_json(json_message):
            return cls(**json_message)
        return None


ExampleMessage.register_to_factory()
