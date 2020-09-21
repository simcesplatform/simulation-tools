# -*- coding: utf-8 -*-
"""
Tests for the ResourceStatesMessages class.
"""
import unittest
import json
import copy

from tools.messages import ResourceStatesMessage
from tools.exceptions.messages import MessageValueError 

from tools.tests.messages_common import FULL_JSON, DEFAULT_TIMESTAMP

# define some test data 
BUS1_ATTRIBUTE = "Bus1"
REAL_POWER_ATTRIBUTE = "RealPower"
REACTIVE_POWER_ATTRIBUTE = "ReactivePower"

DEFAULT_BUS1 = "bus"
DEFAULT_REACTIVE_POWER = 5.0
DEFAULT_REAL_POWER = 100.0

SUBCLASS_JSON = {
    BUS1_ATTRIBUTE: DEFAULT_BUS1,
    REAL_POWER_ATTRIBUTE: DEFAULT_REAL_POWER,
    REACTIVE_POWER_ATTRIBUTE: DEFAULT_REACTIVE_POWER
}

# combine class specific test data with common test data
MESSAGE_JSON = { **FULL_JSON, **SUBCLASS_JSON }

class TestResourceStateMessages(unittest.TestCase):
    """
    Tests for ResourceStatesMessages.
    """

    def test_message_creation(self):
        """Test basic object creation does not produce any errors."""
        message = ResourceStatesMessage(**MESSAGE_JSON)
        
    def test_message_json(self):
        """Test that object can be created from JSON."""
        json = ResourceStatesMessage.from_json( MESSAGE_JSON ).json()
        # check that new object has all subclass specific attributes with correct values.
        for attr in ResourceStatesMessage.MESSAGE_ATTRIBUTES:
            self.assertIn( attr, json )
            self.assertEqual( json[attr], MESSAGE_JSON[attr])
    
    def test_message_bytes(self):
        """Unit test for testing that the bytes conversion works correctly.""" 
        message_full = ResourceStatesMessage.from_json( MESSAGE_JSON )
        message_copy = ResourceStatesMessage.from_json( json.loads(message_full.bytes().decode("UTF-8")) )
        
        self.assertEqual(message_copy.timestamp, message_full.timestamp)
        self.assertEqual(message_copy.message_type, message_full.message_type)
        self.assertEqual(message_copy.simulation_id, message_full.simulation_id)
        self.assertEqual(message_copy.source_process_id, message_full.source_process_id)
        self.assertEqual(message_copy.message_id, message_full.message_id)
        self.assertEqual(message_copy.epoch_number, message_full.epoch_number)
        self.assertEqual(message_copy.last_updated_in_epoch, message_full.last_updated_in_epoch)
        self.assertEqual(message_copy.triggering_message_ids, message_full.triggering_message_ids)
        self.assertEqual(message_copy.warnings, message_full.warnings)
        self.assertEqual( message_copy.bus1, message_full.bus1 )
        self.assertEqual( message_copy.real_power, message_full.real_power )
        self.assertEqual( message_copy.reactive_power, message_full.reactive_power )

    def test_message_equals(self):
        """Test that equals method works correctly."""
        message_full = ResourceStatesMessage( Timestamp=DEFAULT_TIMESTAMP, **MESSAGE_JSON )
        message_copy = ResourceStatesMessage( Timestamp=DEFAULT_TIMESTAMP, **MESSAGE_JSON )
        self.assertEqual( message_full, message_copy )
        # check that when subclass specific attributes have different values
        # objects will not be equal
        DIFFERENT_VALUES = {
            "bus1": "foo",
            "real_power": 200,
            "reactive_power": 10
        }
        
        for attr, value in DIFFERENT_VALUES.items():
            old_value = getattr( message_copy, attr )
            setattr( message_copy, attr, value ) 
            self.assertNotEqual( message_full, message_copy )
            setattr( message_copy, attr, old_value )
            self.assertEqual( message_full, message_copy )
    
    def test_invalid_values(self):
        """Test that invalid attribute values are not accepted.""" 
        invalid_values = {
            "Bus1": 1,
            "ReactivePower": 'foo',
            "RealPower": None
        }
        
        # try to create object with invalid values for each attribute in turn
        for attr, value in invalid_values.items():
            invalid_json = copy.deepcopy( MESSAGE_JSON )
            invalid_json[attr] = value
            with self.subTest( attribute = attr, value = value ):
                with self.assertRaises( MessageValueError ):
                    ResourceStatesMessage( **invalid_json ) 

if __name__ == "__main__":
    unittest.main()