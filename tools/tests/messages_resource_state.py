# -*- coding: utf-8 -*-
"""
Tests for the ResourceStatesMessages class.
"""
import unittest
import json
import copy

from tools.messages import ResourceStateMessage
from tools.exceptions.messages import MessageValueError

from tools.tests.messages_common import DEFAULT_TYPE, FULL_JSON, DEFAULT_TIMESTAMP

# define some test data
BUS_ATTRIBUTE = "Bus"
REAL_POWER_ATTRIBUTE = "RealPower"
REACTIVE_POWER_ATTRIBUTE = "ReactivePower"
NODE_ATTRIBUTE = "Node"

DEFAULT_BUS = "bus"
DEFAULT_REACTIVE_POWER = 5.0
DEFAULT_REAL_POWER = 100.0
DEFAULT_NODE = 2

SUBCLASS_JSON = {
    BUS_ATTRIBUTE: DEFAULT_BUS,
    REAL_POWER_ATTRIBUTE: DEFAULT_REAL_POWER,
    REACTIVE_POWER_ATTRIBUTE: DEFAULT_REACTIVE_POWER,
    NODE_ATTRIBUTE: DEFAULT_NODE
}

DEFAULT_TYPE = "ResourceState"
FULL_JSON = {**FULL_JSON, "Type": DEFAULT_TYPE}

# combine class specific test data with common test data
MESSAGE_JSON = {**FULL_JSON, **SUBCLASS_JSON}
# without optional attributes
MESSAGE_STRIPPED_JSON = copy.deepcopy(MESSAGE_JSON)
del MESSAGE_STRIPPED_JSON[NODE_ATTRIBUTE]


class TestResourceStateMessage(unittest.TestCase):
    """
    Tests for ResourceStateMessage.
    """

    def test_message_type(self):
        """Unit test for the ResourceStateMessage type."""
        self.assertEqual(ResourceStateMessage.CLASS_MESSAGE_TYPE, "ResourceState")
        self.assertEqual(ResourceStateMessage.MESSAGE_TYPE_CHECK, True)

    def test_message_creation(self):
        """Test basic object creation does not produce any errors."""
        # with optional parameter
        message = ResourceStateMessage(**MESSAGE_JSON)
        self.assertIsInstance(message, ResourceStateMessage)
        # without optional parameter
        message = ResourceStateMessage(**MESSAGE_STRIPPED_JSON)
        self.assertIsInstance(message, ResourceStateMessage)

    def test_message_json(self):
        """Test that object can be created from JSON."""
        # test with all attributes
        message_json = ResourceStateMessage.from_json(MESSAGE_JSON).json()
        # check that new object has all subclass specific attributes with correct values.
        for attr in ResourceStateMessage.MESSAGE_ATTRIBUTES:
            with self.subTest(attribute=attr):
                self.assertIn(attr, message_json)
                self.assertEqual(message_json[attr], MESSAGE_JSON[attr])

        # test without optional attributes
        message_json = ResourceStateMessage.from_json(MESSAGE_STRIPPED_JSON).json()
        # check that new object has all subclass specific attributes with correct values.
        for attr in ResourceStateMessage.MESSAGE_ATTRIBUTES:
            with self.subTest(attribute=attr):
                if attr in ResourceStateMessage.OPTIONAL_ATTRIBUTES:
                    continue

                self.assertIn(attr, message_json)
                self.assertEqual(message_json[attr], MESSAGE_JSON[attr])

    def test_message_bytes(self):
        """Unit test for testing that the bytes conversion works correctly."""
        message_full = ResourceStateMessage.from_json(MESSAGE_JSON)
        message_copy = ResourceStateMessage.from_json(json.loads(message_full.bytes().decode("UTF-8")))

        self.assertEqual(message_copy.timestamp, message_full.timestamp)
        self.assertEqual(message_copy.message_type, message_full.message_type)
        self.assertEqual(message_copy.simulation_id, message_full.simulation_id)
        self.assertEqual(message_copy.source_process_id, message_full.source_process_id)
        self.assertEqual(message_copy.message_id, message_full.message_id)
        self.assertEqual(message_copy.epoch_number, message_full.epoch_number)
        self.assertEqual(message_copy.last_updated_in_epoch, message_full.last_updated_in_epoch)
        self.assertEqual(message_copy.triggering_message_ids, message_full.triggering_message_ids)
        self.assertEqual(message_copy.warnings, message_full.warnings)
        self.assertEqual(message_copy.bus, message_full.bus)
        self.assertEqual(message_copy.real_power, message_full.real_power)
        self.assertEqual(message_copy.reactive_power, message_full.reactive_power)
        self.assertEqual(message_copy.node, message_full.node)

    def test_message_equals(self):
        """Test that equals method works correctly."""
        message_full = ResourceStateMessage(Timestamp=DEFAULT_TIMESTAMP, **MESSAGE_JSON)
        message_copy = ResourceStateMessage(Timestamp=DEFAULT_TIMESTAMP, **MESSAGE_JSON)
        self.assertEqual(message_full, message_copy)

        # check that when subclass specific attributes have different values
        # objects will not be equal
        different_values = {
            "bus": "foo",
            "real_power": 200,
            "reactive_power": 10,
            "node": 3
        }

        for attr, value in different_values.items():
            with self.subTest(attribute=attr, value=value):
                old_value = getattr(message_copy, attr)
                setattr(message_copy, attr, value)
                self.assertNotEqual(message_full, message_copy)
                setattr(message_copy, attr, old_value)
                self.assertEqual(message_full, message_copy)

    def test_invalid_values(self):
        """Test that invalid attribute values are not accepted."""
        invalid_values = {
            "Bus": [1],
            "ReactivePower": ['foo'],
            "RealPower": [None],
            "Node": [4, "foo"]
        }

        # try to create object with invalid values for each attribute in turn
        for attr, values in invalid_values.items():
            invalid_json = copy.deepcopy(MESSAGE_JSON)
            for value in values:
                invalid_json[attr] = value
                with self.subTest(attribute=attr, value=value):
                    with self.assertRaises(MessageValueError):
                        ResourceStateMessage(**invalid_json)


if __name__ == "__main__":
    unittest.main()
