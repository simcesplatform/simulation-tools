# -*- coding: utf-8 -*-

"""Unit tests for the classes related to the TimeSeriesBlock."""

import datetime
import json
import random
import string
from typing import Dict, List, Union
import unittest

from tools.datetime_tools import to_iso_format_datetime_string
from tools.exceptions.timeseries import TimeSeriesDateError, TimeSeriesUnitError, TimeSeriesValueError
from tools.timeseries import UnitCode, TimeSeriesAttribute, TimeSeriesBlock


def get_unit_code():
    """Returns a unit code."""
    unit_codes = ["m", "V", "A", "W", "kg"]
    while True:
        yield unit_codes[random.randint(0, len(unit_codes) - 1)]


def get_attribute_name():
    """Returns an attribute name."""
    letters = string.ascii_lowercase
    while True:
        attribute_name = ""
        for _ in range(8):
            attribute_name += letters[random.randint(0, len(letters) - 1)]
        yield attribute_name.capitalize()


def generate_timeseries_values(unit_code: str, n_values: int) \
        -> Dict[str, Union[str, List[Union[int, float, bool, str]]]]:
    """Generates a new timeseries dictionary."""
    value_types = [int, float, bool, str]
    value_type = value_types[random.randint(0, len(value_types) - 1)]
    if isinstance(value_type, int):
        values = [random.randint(-1000, 1000) for _ in range(n_values)]
    elif isinstance(value_type, float):
        values = [random.uniform(-1000.0, 1000.0) for _ in range(n_values)]
    elif isinstance(value_type, bool):
        values = [random.random() >= 0.5 for _ in range(n_values)]
    else:
        values = [next(get_attribute_name()) for _ in range(n_values)]

    return {
        "UnitOfMeasure": unit_code,
        "Values": values
    }


def generate_timeseries_block(start_time: datetime.datetime, n_series: int, series_length: int) -> dict:
    """Return a dictionary for time series block."""
    timeseries_block = {
        "TimeIndex": [],
        "Series": {}
    }
    current_time = start_time
    for series_index in range(series_length):
        if series_index > 0:
            current_time += datetime.timedelta(minutes=random.randint(1, 60))
        timeseries_block["TimeIndex"].append(to_iso_format_datetime_string(current_time))

    for _ in range(n_series):
        timeseries_block["Series"][next(get_attribute_name())] = \
            generate_timeseries_values(next(get_unit_code()), series_length)

    return timeseries_block


class TestUnitCode(unittest.TestCase):
    """Unit tests for the UnitCode class."""

    def test_is_valid(self):
        """Unit test for testing the validity checking of UCUM unit codes."""
        valid_codes = ["m", "ug", "mA", "m3/s", "J", "V", "MW"]
        invalid_codes = ["invalid", "", "mmmm"]

        for valid_code in valid_codes:
            self.assertTrue(UnitCode.is_valid(valid_code))
        for invalid_code in invalid_codes:
            self.assertFalse(UnitCode.is_valid(invalid_code))


class TestTimeSeriesAttribute(unittest.TestCase):
    """Unit tests for the TimeSeriesAttribute class."""

    def test_valid_attributes(self):
        """Unit test for creating TimeSeriesAttribute objects with valid input."""
        test_attributes = [generate_timeseries_values(next(get_unit_code()), 12) for _ in range(20)]

        for test_attribute in test_attributes:
            # test creating object using from_json method
            attribute_object = TimeSeriesAttribute.from_json(test_attribute)
            self.assertIsInstance(attribute_object, TimeSeriesAttribute)
            self.assertEqual(attribute_object.unit_of_measurement, test_attribute["UnitOfMeasure"])
            self.assertEqual(attribute_object.values, test_attribute["Values"])
            self.assertEqual(attribute_object.json(), test_attribute)

            # test creating object using constructor
            attribute_object2 = TimeSeriesAttribute(
                UnitOfMeasure=test_attribute["UnitOfMeasure"],
                Values=test_attribute["Values"]
            )
            self.assertEqual(attribute_object, attribute_object2)

    def test_invalid_attributes(self):
        """Unit test for creating TimeSeriesAttribute objects with invalid input."""
        attribute_valid = {"UnitOfMeasure": "m", "Values": [1, 2, 3]}
        attribute_missing_unit = {"Values": [1, 2, 3]}
        attribute_missing_values = {"UnitOfMeasure": "m"}
        attribute_invalid_unit = {"UnitOfMeasure": "mmmm", "Values": [1, 2, 3]}
        attribute_invalid_values = {"UnitOfMeasure": "m", "Values": [[], []]}
        attribute_inconsistent_values1 = {"UnitOfMeasure": "m", "Values": [1, 2, 3.0]}
        attribute_inconsistent_values2 = {"UnitOfMeasure": "m", "Values": [1, "2", 3]}
        attribute_inconsistent_values3 = {"UnitOfMeasure": "m", "Values": [True, False, 3]}

        self.assertIsInstance(TimeSeriesAttribute.from_json(attribute_valid), TimeSeriesAttribute)
        self.assertIsNone(TimeSeriesAttribute.from_json(attribute_missing_unit))
        self.assertIsNone(TimeSeriesAttribute.from_json(attribute_missing_values))
        self.assertIsNone(TimeSeriesAttribute.from_json(attribute_invalid_unit))
        self.assertIsNone(TimeSeriesAttribute.from_json(attribute_invalid_values))
        self.assertIsNone(TimeSeriesAttribute.from_json(attribute_inconsistent_values1))
        self.assertIsNone(TimeSeriesAttribute.from_json(attribute_inconsistent_values2))
        self.assertIsNone(TimeSeriesAttribute.from_json(attribute_inconsistent_values3))

        self.assertRaises(TimeSeriesUnitError, TimeSeriesAttribute, **attribute_missing_unit)
        self.assertRaises(TimeSeriesValueError, TimeSeriesAttribute, **attribute_missing_values)
        self.assertRaises(TimeSeriesUnitError, TimeSeriesAttribute, **attribute_invalid_unit)
        self.assertRaises(TimeSeriesValueError, TimeSeriesAttribute, **attribute_invalid_values)
        self.assertRaises(TimeSeriesValueError, TimeSeriesAttribute, **attribute_inconsistent_values1)
        self.assertRaises(TimeSeriesValueError, TimeSeriesAttribute, **attribute_inconsistent_values2)
        self.assertRaises(TimeSeriesValueError, TimeSeriesAttribute, **attribute_inconsistent_values3)


class TestTimeSeriesBlock(unittest.TestCase):
    """Unit tests for the TimeSeriesBlock class."""

    def test_valid_blocks(self):
        """Unit test for creating TimeSeriesBlock objects with valid input."""
        test_blocks = [
            generate_timeseries_block(datetime.datetime.utcnow(), index, 24)
            for index in range(1, 21)
        ]

        for test_block in test_blocks:
            # test creating object using from_json method
            attribute_object = TimeSeriesBlock.from_json(test_block)
            self.assertIsInstance(attribute_object, TimeSeriesBlock)
            self.assertEqual(attribute_object.time_index, test_block["TimeIndex"])

            attribute_series_names = list(test_block["Series"].keys())
            object_series_names = list(attribute_object.series.keys())
            self.assertEqual(object_series_names, attribute_series_names)
            for series_name in attribute_series_names:
                self.assertEqual(attribute_object.series[series_name].json(), test_block["Series"][series_name])
            self.assertEqual(attribute_object.json(), test_block)
            self.assertEqual(str(attribute_object), json.dumps(test_block))

            # test creating object using constructor
            attribute_object2 = TimeSeriesBlock(
                TimeIndex=test_block["TimeIndex"],
                Series=test_block["Series"]
            )
            self.assertEqual(attribute_object2, attribute_object)

            # test adding additional series by add_series method
            series_names = list(test_block["Series"].keys())
            attribute_object3 = TimeSeriesBlock(
                TimeIndex=test_block["TimeIndex"],
                Series={series_names[0]: test_block["Series"][series_names[0]]}
            )
            for series_name in series_names[1:]:
                attribute_object3.add_series(
                    series_name, TimeSeriesAttribute(**test_block["Series"][series_name]))
            self.assertEqual(attribute_object3, attribute_object)

    def test_invalid_blocks(self):
        """Unit test for creating TimeSeriesBlock objects with invalid input."""
        time_index_valid_3 = ["2020-01-01T00:00:00Z", "2020-01-01T01:00:00Z", "2020-01-01T02:00:00Z"]
        time_index_valid_4 = ["2020-01-01T00:00:00Z", "2020-01-01T01:00:00Z", "2020-01-01T02:00:00Z",
                              "2020-01-01T03:00:00Z"]
        invalid_time_index = ["2020-01-01T00:00:00Z", "2020-01-01T01:00:00Z", "invalid"]

        attribute_valid_3 = {"UnitOfMeasure": "m", "Values": [1, 2, 3]}
        attribute_valid_4 = {"UnitOfMeasure": "m", "Values": [1, 2, 3, 4]}
        invalid_attribute = {"UnitOfMeasure": "m", "Values": [1, 2.0, "3"]}

        valid_block_3 = {"TimeIndex": time_index_valid_3, "Series": {"X": attribute_valid_3, "Y": attribute_valid_3}}
        valid_block_4 = {"TimeIndex": time_index_valid_4, "Series": {"X": attribute_valid_4, "Y": attribute_valid_4}}

        block_missing_timeindex = {"Series": {"X": attribute_valid_3, "Y": attribute_valid_3}}
        block_missing_series1 = {"TimeIndex": time_index_valid_3}
        block_missing_series2 = {"TimeIndex": time_index_valid_3, "Series": {}}
        block_invalid_timeindex = {"TimeIndex": invalid_time_index, "Series": {"X": attribute_valid_3}}
        block_invalid_series = {"TimeIndex": time_index_valid_3, "Series": {"X": invalid_attribute}}
        block_different_length1 = {"TimeIndex": time_index_valid_3, "Series": {"X": attribute_valid_4}}
        block_different_length2 = {"TimeIndex": time_index_valid_4, "Series": {"X": attribute_valid_3}}

        valid_object_3 = TimeSeriesBlock.from_json(valid_block_3)
        valid_object_4 = TimeSeriesBlock.from_json(valid_block_4)
        self.assertIsInstance(valid_object_3, TimeSeriesBlock)
        self.assertIsInstance(valid_object_4, TimeSeriesBlock)

        self.assertIsNone(TimeSeriesBlock.from_json(block_missing_timeindex))
        self.assertIsNone(TimeSeriesBlock.from_json(block_missing_series1))
        self.assertIsNone(TimeSeriesBlock.from_json(block_missing_series2))
        self.assertIsNone(TimeSeriesBlock.from_json(block_invalid_timeindex))
        self.assertIsNone(TimeSeriesBlock.from_json(block_invalid_series))
        self.assertIsNone(TimeSeriesBlock.from_json(block_different_length1))
        self.assertIsNone(TimeSeriesBlock.from_json(block_different_length2))

        self.assertRaises(TimeSeriesDateError, TimeSeriesBlock, **block_missing_timeindex)
        self.assertRaises(TimeSeriesValueError, TimeSeriesBlock, **block_missing_series1)
        self.assertRaises(TimeSeriesValueError, TimeSeriesBlock, **block_missing_series2)
        self.assertRaises(TimeSeriesDateError, TimeSeriesBlock, **block_invalid_timeindex)
        self.assertRaises(TimeSeriesValueError, TimeSeriesBlock, **block_invalid_series)
        self.assertRaises(TimeSeriesValueError, TimeSeriesBlock, **block_different_length1)
        self.assertRaises(TimeSeriesValueError, TimeSeriesBlock, **block_different_length2)

        self.assertRaises(TimeSeriesDateError, setattr, valid_object_3, "time_index", time_index_valid_4)
        self.assertRaises(TimeSeriesValueError, setattr, valid_object_3, "series", {"X": attribute_valid_4})
        self.assertRaises(TimeSeriesDateError, setattr, valid_object_4, "time_index", time_index_valid_3)
        self.assertRaises(TimeSeriesValueError, setattr, valid_object_4, "series", {"X": attribute_valid_3})

        self.assertRaises(TimeSeriesValueError, valid_object_3.add_series,
                          "Z", TimeSeriesAttribute(**attribute_valid_4))
        self.assertRaises(TimeSeriesValueError, valid_object_4.add_series,
                          "Z", TimeSeriesAttribute(**attribute_valid_3))


if __name__ == '__main__':
    unittest.main()