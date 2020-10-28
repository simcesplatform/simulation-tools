# -*- coding: utf-8 -*-
'''
Defines various message attribute value blocks that different kinds of messages can use.
'''

import json
from typing import Union, Dict, Any

from tools.exceptions.messages import MessageValueError
from tools.tools import FullLogger

LOGGER = FullLogger(__name__)


class QuantityBlock():
    '''
    Represents a float type value and associated measurement unit.
    '''

    # name of block attribute which contains the number value
    VALUE_ATTRIBUTE = 'Value'
    # name of the block attribute which contains the unit of measurement.
    UNIT_OF_MEASURE_ATTRIBUTE = 'UnitOfMeasure'

    def __init__(self, **kwargs):
        '''Create a QuantityBlock from the given Value and UnitOfMeasure.
        Raises MessageValueError if value or measurement unit are missing or invalid.'''
        self.value = kwargs.get(self.VALUE_ATTRIBUTE, None)
        self.unit_of_measure = kwargs.get(self.UNIT_OF_MEASURE_ATTRIBUTE, None)

    @property
    def value(self) -> float:
        '''
        Get the value of the quantity.
        '''
        return self._value

    @property
    def unit_of_measure(self) -> str:
        '''
        Get the unit of measure of the quantity.
        '''
        return self._unit_of_measure

    @value.setter
    def value(self, value: float):
        '''
        Set the value for the quantity.
        Raises MessageValueError if the value is invalid.
        '''
        if value is None:
            raise MessageValueError('Quantity block value cannot be None')

        try:
            self._value = float(value)

        except ValueError:
            raise MessageValueError(f'Unable to convert {value} to float for quantity block value.')

    @unit_of_measure.setter
    def unit_of_measure(self, unit_of_measure: str):
        '''
        Set the unit of measure for the quantity.
        Raises MessageValueError if the unit is None.
        '''
        if unit_of_measure is None:
            raise MessageValueError('Unit of measure for quantity block cannot be None')

        self._unit_of_measure = str(unit_of_measure)

    def json(self) -> Dict[str, Union[float, str]]:
        '''
        Convert the quantity block to a dictionary.
        '''
        return {self.VALUE_ATTRIBUTE: self.value, self.UNIT_OF_MEASURE_ATTRIBUTE: self.unit_of_measure}

    def __eq__(self, other):
        '''
        Check that two quantity blocks represent the same quantity.
        '''
        return (isinstance(other, QuantityBlock) and
                self.value == other.value and
                self.unit_of_measure == other.unit_of_measure)

    def __str__(self) -> str:
        '''
        Convert to a string.
        '''
        return json.dumps(self.json())

    @classmethod
    def validate_json(cls, json_quantity_block: Dict[str, Any]) -> bool:
        '''
        Check if the given dictionary could be converted to a QuantityBlock.
        '''
        try:
            QuantityBlock(**json_quantity_block)
            return True

        except MessageValueError as err:
            LOGGER.warning("{:s} error '{:s}' encountered when validating quantity block".format(
                str(type(err)), str(err)))
            return False

    @classmethod
    def from_json(cls, json_quantity_block: Dict[str, Any]):
        '''
        Convert the given dictionary to a QuantityBlock.
        If the conversion does not succeed returns None.
        '''
        if cls.validate_json(json_quantity_block):
            return QuantityBlock(**json_quantity_block)

        return None
