# -*- coding: utf-8 -*-

"""This module contains a classes for handling time series data for the messages in the simulation platform."""

import datetime

import isodate

from tools.datetime_tools import to_iso_format_datetime_string
from tools.tools import FullLogger

LOGGER = FullLogger(__name__)


class TimeSeriesAttribute:
    """Class for containing one time series attribute within a TimeSeriesBlock."""
    def __init__(self, unit_of_measurement: str, values: list):
        # TODO: add checks for the parameters
        self.__unit_of_measurement = unit_of_measurement
        self.__values = values

    @property
    def unit_of_measurement(self):
        """The unit of measurement for the time series attribute."""
        return self.__unit_of_measurement

    @property
    def values(self):
        """The value list for the time series attribute."""
        return self.__values

    def json(self):
        """Returns the time series attribute as JSON object"""
        return {
            "UnitOfMeasure": self.unit_of_measurement,
            "Values": self.values
        }


class TimeSeriesBlock():
    """Class for containing one time series block for a message in the simulation platform. """
    def __init__(self, start_time: datetime.datetime, time_interval: datetime.timedelta, **timeseries_attributes):
        # TODO: add checks for the parameters
        self.__start_time = to_iso_format_datetime_string(start_time)
        self.__time_interval = isodate.duration_isoformat(time_interval)
        self.__time_series_attributes = {}
        for timeseries_attribute_name, timeseries_attribute_value in timeseries_attributes.items():
            if isinstance(timeseries_attribute_value, TimeSeriesAttribute):
                self.__time_series_attributes[timeseries_attribute_name] = timeseries_attribute_value

    @property
    def start_time(self):
        """The start time (UTC) for the time series in ISO 8601 date and time format."""
        return self.__start_time

    @property
    def time_interval(self):
        """The time interval between each time series points in ISO 8601 duration format."""
        return self.__time_interval

    @property
    def attributes(self):
        """The list of time series attribute names."""
        return list(self.__time_series_attributes.keys())

    @property
    def attribute(self, attribute_name):
        """The time series attribute value for the given attribute. None, if the attribute does not exist."""
        return self.__time_series_attributes.get(attribute_name, None)

    def add_attribute(self, new_attribute_name: str, new_attribute_value: TimeSeriesAttribute):
        """Adds a new timeseries attribute to the timeseries block.
           Replaces any earlier attributes with the same name."""
        # TODO: add checks to the parameters
        self.__time_series_attributes[new_attribute_name] = new_attribute_value

    def json(self):
        """Returns the timeseries block as a JSON object."""
        return {
            "StartTime": self.start_time,
            "Interval": self.time_interval,
            "Series": {
                attribute_name: attribute_value.json()
                for attribute_name, attribute_value in self.__time_series_attributes.items()
            }
        }
