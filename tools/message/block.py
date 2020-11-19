# -*- coding: utf-8 -*-
"""
Defines various message attribute value blocks that different kinds of messages can use.
"""

from __future__ import annotations
import collections
import datetime
import json
from typing import Any, Dict, List, Union

from tools.datetime_tools import to_iso_format_datetime_string
from tools.exceptions.messages import MessageValueError
from tools.exceptions.timeseries import TimeSeriesError, TimeSeriesDateError, TimeSeriesUnitError, TimeSeriesValueError
from tools.message.unit import UnitCode
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

    def __repr__(self) -> str:
        return self.__str__()

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


class TimeSeriesAttribute:
    """Class for containing one time series attribute within a TimeSeriesBlock."""
    # By default the unit code validator is not in use.
    UNIT_CODE_VALIDATION = False

    TIMESERIES_ATTRIBUTES = {
        "UnitOfMeasure": "unit_of_measurement",
        "Values": "values"
    }

    def __init__(self, **kwargs):
        """Only attributes "UnitOfMeasure" and "Values" are considered.
           If either attribute contains invalid values, throws an instance of TimeSeriesError.
        """
        for json_attribute_name in TimeSeriesAttribute.TIMESERIES_ATTRIBUTES:
            setattr(self, TimeSeriesAttribute.TIMESERIES_ATTRIBUTES[json_attribute_name],
                    kwargs.get(json_attribute_name, None))

    @property
    def unit_of_measurement(self) -> str:
        """The unit of measurement for the time series."""
        return self.__unit_of_measurement

    @property
    def values(self) -> Union[List[bool], List[int], List[float], List[str]]:
        """The values for the time series."""
        return self.__values

    @unit_of_measurement.setter
    def unit_of_measurement(self, unit_of_measurement: str):
        if not self._check_unit_of_measurement(unit_of_measurement):
            raise TimeSeriesUnitError("'{:s}' is not an allowed unit of measurement".format(str(unit_of_measurement)))
        self.__unit_of_measurement = unit_of_measurement

    @values.setter
    def values(self, values: Union[List[bool], List[int], List[float], List[str]]):
        if not self._check_values(values):
            raise TimeSeriesValueError("'{:s}' is not a valid time series value list".format(str(values)))
        self.__values = values

    @classmethod
    def _check_unit_of_measurement(cls, unit_of_measurement: str) -> bool:
        return (
            isinstance(unit_of_measurement, str) and
            (not cls.UNIT_CODE_VALIDATION or UnitCode.is_valid(unit_of_measurement))
        )

    @classmethod
    def _check_values(cls, values: Union[List[bool], List[int], List[float], List[str]]) -> bool:
        if not isinstance(values, list):
            return False
        if not values:  # accept empty list
            return True

        value_type = type(values[0])
        for value in values:
            # Check that all the values in the list are of the same type.
            if not isinstance(value, (bool, int, float, str)) or not isinstance(value, value_type):
                return False
        return True

    def json(self) -> Dict[str, Any]:
        """Returns the time series attribute as JSON object."""
        return {
            json_attribute_name: getattr(self, object_attribute_name)
            for json_attribute_name, object_attribute_name in TimeSeriesAttribute.TIMESERIES_ATTRIBUTES.items()
        }

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, TimeSeriesAttribute) and
            self.unit_of_measurement == other.unit_of_measurement and
            self.values == other.values
        )

    def __str__(self) -> str:
        return json.dumps(self.json())

    def __repr__(self) -> str:
        return self.__str__()

    @classmethod
    def validate_json(cls, json_timeseries: Dict[str, Any]) -> bool:
        """Validates the given the given json object for the attributes covered in TimeSeriesAttribute class.
           Returns True if the time series is ok. Otherwise, return False."""
        if not isinstance(json_timeseries, dict):
            return False

        for json_attribute_name, object_attribute_name in cls.TIMESERIES_ATTRIBUTES.items():
            if json_attribute_name not in json_timeseries:
                LOGGER.warning("{:s} attribute is missing from the time series".format(json_attribute_name))
                return False

            if not getattr(
                    cls,
                    "_".join(["_check", object_attribute_name]))(json_timeseries[json_attribute_name]):
                LOGGER.warning("'{:s}' is not valid value for {:s}".format(
                    str(json_timeseries[json_attribute_name]), json_attribute_name))
                return False

        return True

    @classmethod
    def from_json(cls, json_timeseries: Dict[str, Any]) -> Union[TimeSeriesAttribute, None]:
        """Returns a class object created based on the given JSON attributes.
           If the given JSON is contains invalid values, returns None."""
        if cls.validate_json(json_timeseries):
            return cls(**json_timeseries)
        return None


class TimeSeriesBlock():
    """Class for containing one time series block for a message in the simulation platform. """
    TIMEINDEX_ATTRIBUTE = "TimeIndex"
    SERIES_ATTRIBUTE = "Series"

    TIMESERIES_BLOCK_ATTRIBUTES = collections.OrderedDict({
        TIMEINDEX_ATTRIBUTE: "time_index",
        SERIES_ATTRIBUTE: "series"
    })

    def __init__(self, **kwargs):
        """Only attributes "TimeIndex" and "Series" are considered.
           If either attribute contains invalid values, throws an instance of TimeSeriesError.
        """
        for json_attribute_name in TimeSeriesBlock.TIMESERIES_BLOCK_ATTRIBUTES:
            setattr(self, TimeSeriesBlock.TIMESERIES_BLOCK_ATTRIBUTES[json_attribute_name],
                    kwargs.get(json_attribute_name, None))

    @property
    def time_index(self) -> List[str]:
        """The list of date times for the time series in ISO 8601 format (UTC)."""
        return self.__time_index

    @property
    def series(self) -> Dict[str, TimeSeriesAttribute]:
        """The list of the time series values as dictionary with the series name as keys and
           TimeSeriesAttribute objects as values."""
        return self.__series

    def get_single_series(self, series_name: str) -> Union[TimeSeriesAttribute, None]:
        """Returns the corresponding time series values as a TimeSeriesAttribute object.
           Returns None if the series does not exist."""
        return self.__series.get(series_name, None)

    @time_index.setter
    def time_index(self, time_index: List[Union[str, datetime.datetime]]):
        if getattr(self, "series", None) is None:
            expected_list_length = None
        else:
            # Check that the time series list is the same length as the first value series list.
            expected_list_length = len(self.get_single_series(next(iter(self.series))).values)

        if self._check_time_index(time_index, expected_list_length):
            new_time_index_list = []
            for datetime_value in time_index:
                iso_format_string = to_iso_format_datetime_string(datetime_value)
                if isinstance(iso_format_string, str):
                    new_time_index_list.append(iso_format_string)
                else:
                    raise TimeSeriesDateError("'{:s}' is not a valid date time value".format(str(datetime_value)))
            self.__time_index = new_time_index_list

        else:
            raise TimeSeriesDateError("'{:s}' is not a valid list of date times".format(str(time_index)))

    @series.setter
    def series(self, series: Dict[str, Union[TimeSeriesAttribute, dict]]):
        if getattr(self, "time_index", None) is None:
            expected_list_length = None
        else:
            # Check that all the values series lists are the same length as the time series list.
            expected_list_length = len(self.time_index)

        if not self._check_series(series, expected_list_length):
            raise TimeSeriesValueError("'{:s}' is not a valid dictionary of time series values".format(str(series)))

        self.__series = {}
        for series_name, series_values in series.items():
            if isinstance(series_values, TimeSeriesAttribute):
                self.__series[series_name] = series_values
            else:
                attribute_series = TimeSeriesAttribute.from_json(series_values)
                if attribute_series is not None:
                    self.__series[series_name] = attribute_series

    def add_series(self, series_name: str, series_values: TimeSeriesAttribute):
        """Adds a new or replaces an old value series for the TimeSeriesBlock."""
        if self._check_series({series_name: series_values}, len(self.__time_index)):
            self.series[series_name] = series_values
        else:
            raise TimeSeriesValueError("'{:s}' is not a valid value series for {:s}".format(
                str(series_name), str(series_values)))

    @classmethod
    def _check_time_index(cls, time_index: List[Union[str, datetime.datetime]], list_length: int = None) -> bool:
        if not isinstance(time_index, list):
            return False
        if list_length is not None and len(time_index) != list_length:
            return False

        for datetime_value in time_index:
            try:
                if to_iso_format_datetime_string(datetime_value) is None:
                    return False
            except ValueError:
                return False

        return True

    @classmethod
    def _check_series(cls, series: Dict[str, Union[TimeSeriesAttribute, dict]], list_length: int = None) -> bool:
        if not isinstance(series, dict) or len(series) == 0:
            return False

        for series_name, series_values in series.items():
            if not isinstance(series_name, str) or len(series_name) == 0:
                return False

            if isinstance(series_values, TimeSeriesAttribute):
                if list_length is not None and len(series_values.values) != list_length:
                    return False
            else:
                timeseries_attribute = TimeSeriesAttribute.from_json(series_values)
                if (timeseries_attribute is None or
                        (list_length is not None and len(timeseries_attribute.values) != list_length)):
                    return False

        return True

    def json(self) -> Dict[str, Any]:
        """Returns the timeseries block as a JSON object."""
        return {
            self.TIMEINDEX_ATTRIBUTE: self.time_index,
            self.SERIES_ATTRIBUTE: {
                attribute_name: attribute_value.json()
                for attribute_name, attribute_value in self.series.items()
            }
        }

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, TimeSeriesBlock) and
            self.time_index == other.time_index and
            self.series == other.series
        )

    def __str__(self) -> str:
        return json.dumps(self.json())

    def __repr__(self) -> str:
        return self.__str__()

    @classmethod
    def validate_json(cls, json_timeseries_block: Dict[str, Any]) -> bool:
        """Validates the given the given json object for the attributes covered in TimeSeriesBlock class.
           Returns True if the time series block is ok. Otherwise, return False."""
        try:
            _ = cls(**json_timeseries_block)
            return True

        except TimeSeriesError as time_series_error:
            LOGGER.warning("{:s} error '{:s}' encountered when validating time series block".format(
                str(type(time_series_error)), str(time_series_error)))
            return False

    @classmethod
    def from_json(cls, json_timeseries_block: Dict[str, Any]) -> Union[TimeSeriesBlock, None]:
        """Returns a class object created based on the given JSON attributes.
           If the given JSON is not validated returns None."""
        if cls.validate_json(json_timeseries_block):
            return cls(**json_timeseries_block)
        return None
