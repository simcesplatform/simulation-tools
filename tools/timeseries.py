# -*- coding: utf-8 -*-

"""This module contains a classes for handling time series data for the messages in the simulation platform."""

import collections
import csv
import pathlib

from tools.datetime_tools import to_iso_format_datetime_string
from tools.exceptions.timeseries import TimeSeriesError, TimeSeriesDateError, TimeSeriesUnitError, TimeSeriesValueError
from tools.tools import FullLogger

LOGGER = FullLogger(__name__)


class UnitCode:
    """Class for verifying a string as a valid UCUM (The Unified Code for Units of Measure) code."""
    UNIT_CODE_FILE_PATH = "resources"
    UNIT_CODE_FILE_NAME = "unit_codes.csv"
    UNIT_CODE_FILE_COLUMN_SEPARATOR = ";"
    UNIT_CODE_FILE_CODE_COLUMN = "Code"
    UNIT_CODE_FILE_DESCRIPTION_COLUMN = "Description"

    UNIT_CODE_LIST = {}

    @classmethod
    def is_valid(cls, unit_code: str):
        """Returns True if unit_code is a valid UCUM code.
           Only codes listed in https://www.hl7.org/fhir/valueset-ucum-units.html are considered as valid."""
        if not cls.UNIT_CODE_LIST:
            cls.UNIT_CODE_LIST = cls.__return_unit_code_list()

        return unit_code in cls.UNIT_CODE_LIST

    @classmethod
    def get_description(cls, unit_code: str):
        """Returns the description for the given unit code. Return None if the code is not valid."""
        if not cls.UNIT_CODE_LIST:
            cls.UNIT_CODE_LIST = cls.__return_unit_code_list()

        return cls.UNIT_CODE_LIST.get(unit_code, None)

    @classmethod
    def __return_unit_code_list(cls):
        unit_code_dict = {}

        current_path = pathlib.Path(".")
        for unit_code_file in current_path.glob("/".join(["**", cls.UNIT_CODE_FILE_PATH, cls.UNIT_CODE_FILE_NAME])):
            try:
                with open(unit_code_file, mode="r") as csv_file:
                    csv_reader = csv.DictReader(csv_file, delimiter=";")
                    for csv_row in csv_reader:
                        unit_code = csv_row[cls.UNIT_CODE_FILE_CODE_COLUMN]
                        unit_description = csv_row[cls.UNIT_CODE_FILE_DESCRIPTION_COLUMN]

                        unit_code_dict[unit_code] = unit_description

            except KeyError as key_error:
                LOGGER.error("KeyError '{:s}' while trying to read unit codes from file {:s}".format(
                    str(key_error), unit_code_file))

            except csv.Error as csv_error:
                LOGGER.error("csv.Error '{:s}' while trying to read unit codes from file {:s}".format(
                    str(csv_error), unit_code_file))

        return unit_code_dict


class TimeSeriesAttribute:
    """Class for containing one time series attribute within a TimeSeriesBlock."""
    TIMESERIES_ATTRIBUTES = {
        "UnitOfMeasure": "unit_of_measurement",
        "Values": "values"
    }

    def __init__(self, **kwargs):
        """Only attributes "UnitOfMeasure" and "Values" are considered."""
        for json_attribute_name in TimeSeriesAttribute.TIMESERIES_ATTRIBUTES:
            setattr(self, TimeSeriesAttribute.TIMESERIES_ATTRIBUTES[json_attribute_name],
                    kwargs.get(json_attribute_name, None))

    @property
    def unit_of_measurement(self):
        """The unit of measurement for the time series."""
        return self.__unit_of_measurement

    @property
    def values(self):
        """The values for the time series."""
        return self.__values

    @unit_of_measurement.setter
    def unit_of_measurement(self, unit_of_measurement):
        if not self._check_unit_of_measurement(unit_of_measurement):
            raise TimeSeriesUnitError("'{:s}' is not an allowed unit of measurement".format(str(unit_of_measurement)))
        self.__unit_of_measurement = unit_of_measurement

    @values.setter
    def values(self, values):
        if not self._check_values(values):
            raise TimeSeriesValueError("'{:s}' is not a valid time series value list".format(str(values)))
        self.__values = values

    @classmethod
    def _check_unit_of_measurement(cls, unit_of_measurement):
        return isinstance(unit_of_measurement, str) and UnitCode.is_valid(unit_of_measurement)

    @classmethod
    def _check_values(cls, values):
        if not isinstance(values, (list, tuple)):
            return False
        for value in values:
            if not isinstance(value, (bool, int, float, str)):
                return False
        return True

    def json(self):
        """Returns the time series attribute as JSON object"""
        return {
            json_attribute_name: getattr(self, object_attribute_name)
            for json_attribute_name, object_attribute_name in TimeSeriesAttribute.TIMESERIES_ATTRIBUTES.items()
        }

    @classmethod
    def validate_json(cls, json_timeseries: dict):
        """Validates the given the given json object for the attributes covered in TimeSeriesAttribute class.
           Returns True if the time series is ok. Otherwise, return False."""
        for json_attribute_name, object_attribute_name in TimeSeriesAttribute.TIMESERIES_ATTRIBUTES.items():
            if json_attribute_name not in json_timeseries:
                LOGGER.warning("{:s} attribute is missing from the time series".format(json_attribute_name))
                return False

            if not getattr(
                    TimeSeriesAttribute,
                    "_".join(["_check", object_attribute_name]))(json_timeseries[json_attribute_name]):
                LOGGER.warning("'{:s}' is not valid value for {:s}".format(
                    str(json_timeseries[json_attribute_name]), json_attribute_name))
                return False

        return True

    @classmethod
    def from_json(cls, json_timeseries: dict):
        """Returns a class object created based on the given JSON attributes.
           If the given JSON is not validated returns None."""
        if cls.validate_json(json_timeseries):
            return cls(**json_timeseries)
        return None


class TimeSeriesBlock():
    """Class for containing one time series block for a message in the simulation platform. """
    TIMESERIES_BLOCK_ATTRIBUTES = collections.OrderedDict({
        "TimeIndex": "time_index",
        "Series": "series"
    })

    def __init__(self, **kwargs):
        """Only attributes "TimeIndex" and "Series" are considered."""
        for json_attribute_name in TimeSeriesBlock.TIMESERIES_BLOCK_ATTRIBUTES:
            setattr(self, TimeSeriesBlock.TIMESERIES_BLOCK_ATTRIBUTES[json_attribute_name],
                    kwargs.get(json_attribute_name, None))

    @property
    def time_index(self):
        """The list of date times for the time series in ISO 8601 format (UTC)."""
        return self.__time_index

    @property
    def series(self):
        """The list of the time series values as dictionary with the series name as keys and
           TimeSeriesAttribute objects as values."""
        return self.__series

    def get_single_series(self, series_name: str):
        """Returns the corresponding time series values as a TimeSeriesAttribute object.
           Returns None if the series does not exist."""
        return self.__series.get(series_name, None)

    @time_index.setter
    def time_index(self, time_index):
        if getattr(self, "series", None) is None:
            expected_list_length = None
        else:
            expected_list_length = len(self.get_single_series(next(iter(self.series))).values)

        if not self._check_time_index(time_index, expected_list_length):
            raise TimeSeriesDateError("'{:s}' is not a valid list of date times".format(str(time_index)))
        self.__time_index = [
            to_iso_format_datetime_string(datetime_value)
            for datetime_value in time_index
        ]

    @series.setter
    def series(self, series):
        if getattr(self, "time_index", None) is None:
            expected_list_length = None
        else:
            expected_list_length = len(self.time_index)

        if not self._check_series(series, expected_list_length):
            raise TimeSeriesValueError("'{:s}' is not a valid dictionary of time series values".format(str(series)))
        self.__series = {
            series_name: (
                series_values if isinstance(series_values, TimeSeriesAttribute)
                else TimeSeriesAttribute.from_json(series_values))
            for series_name, series_values in series.items()
        }

    def add_series(self, series_name: str, series_values: TimeSeriesAttribute):
        """Adds a new or replaces an old time series for the TimeSeriesBlock."""
        if self._check_series({series_name: series_values}):
            self.series[series_name] = series_values
        else:
            raise TimeSeriesValueError("'{:s}' is not a valid value series for {:s}".format(
                str(series_name), str(series_values)))

    @classmethod
    def _check_time_index(cls, time_index, list_length=None):
        if not isinstance(time_index, (list, tuple)):
            return False
        if list_length is not None and len(time_index) != list_length:
            return False

        for datetime_value in time_index:
            if to_iso_format_datetime_string(datetime_value) is None:
                return False

        return True

    @classmethod
    def _check_series(cls, series, list_length=None):
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

    def json(self):
        """Returns the timeseries block as a JSON object."""
        return {
            "TimeIndex": self.time_index,
            "Series": {
                attribute_name: attribute_value.json()
                for attribute_name, attribute_value in self.series.items()
            }
        }

    @classmethod
    def validate_json(cls, json_timeseries_block: dict):
        """Validates the given the given json object for the attributes covered in TimeSeriesBlock class.
           Returns True if the time series block is ok. Otherwise, return False."""
        try:
            _ = TimeSeriesBlock(**json_timeseries_block)
            return True

        except TimeSeriesError as time_series_error:
            LOGGER.warning("{:s} error '{:s}' encountered when validating time series block".format(
                str(type(time_series_error)), str(time_series_error)))
            return False

    @classmethod
    def from_json(cls, json_timeseries_block: dict):
        """Returns a class object created based on the given JSON attributes.
           If the given JSON is not validated returns None."""
        if cls.validate_json(json_timeseries_block):
            return cls(**json_timeseries_block)
        return None
