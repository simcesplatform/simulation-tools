# -*- coding: utf-8 -*-

"""Unit tests for the classes related to the TimeSeriesBlock."""

import unittest

from tools.timeseries import UnitCode, TimeSeriesAttribute, TimeSeriesBlock


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

    def test_a(self):
        """Unit test for ..."""


class TestTimeSeriesBlock(unittest.TestCase):
    """Unit tests for the TimeSeriesBlock class."""

    def test_a(self):
        """Unit test for ..."""


if __name__ == '__main__':
    unittest.main()
