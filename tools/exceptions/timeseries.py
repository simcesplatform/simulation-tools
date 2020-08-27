# -*- coding: utf-8 -*-

"""This module contains the exception classes for the time series blocks."""

from tools.tools import FullLogger

from tools.exceptions.messages import MessageError

LOGGER = FullLogger(__name__)


class TimeSeriesError(MessageError):
    """The base exception class for errors related to time series block."""


class TimeSeriesDateError(TimeSeriesError):
    """Exception class for errors related to invalid datetimes in time series block."""


class TimeSeriesUnitError(TimeSeriesError):
    """Exception class for errors related to invalid unit of measurement in time series block."""


class TimeSeriesValueError(TimeSeriesError):
    """Exception class for errors related to invalid values in time series block."""
