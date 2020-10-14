# -*- coding: utf-8 -*-

"""Unit test for the MessageCallback class."""

import asyncio
import json
from typing import Union

import aiounittest
import aio_pika.message
import pamqp
import pamqp.specification

from tools.callbacks import MessageCallback
from tools.messages import BaseMessage, EpochMessage, GeneralMessage, \
                           ResultMessage, SimulationStateMessage, StatusMessage, ResourceStateMessage
from tools.tests.messages_abstract import ALTERNATE_JSON, DEFAULT_TIMESTAMP, FULL_JSON, MESSAGE_TYPE_ATTRIBUTE
from tools.tests.messages_resource_state import MESSAGE_JSON as RESOURCE_STATES_MESSAGE_JSON

# Add the attributes from ResourceState message to the full test messages
FULL_JSON = {**RESOURCE_STATES_MESSAGE_JSON, **FULL_JSON}
ALTERNATE_JSON = {**RESOURCE_STATES_MESSAGE_JSON, **ALTERNATE_JSON}

FAIL_TEST_JSON = {
    "test": "fail"
}
FAIL_TEST_STR = '{"test" "fail"}'


def get_incoming_message(body, routing_key) -> aio_pika.message.IncomingMessage:
    """Returns a dummy incoming message withough the message for the use of the unit tests."""
    delivered_message = aio_pika.message.DeliveredMessage(
        delivery=pamqp.specification.Basic.Deliver(routing_key=routing_key),
        header=pamqp.ContentHeader(),
        body=body,
        channel=1)
    return aio_pika.message.IncomingMessage(delivered_message)


class DummyHandler:
    """Class for dummy message handler."""
    def __init__(self):
        self.last_message = None
        self.last_topic = None

    async def message_handler(self, message_object, message_topic):
        """Stores the received message and topic."""
        self.last_message = message_object
        self.last_topic = message_topic


HANDLER = DummyHandler()


class TestMessageCallback(aiounittest.AsyncTestCase):
    """Unit tests for the MessageCallback class."""
    GENERAL_MESSAGE = GeneralMessage(Timestamp=DEFAULT_TIMESTAMP, **FULL_JSON)
    GENERAL_JSON = GENERAL_MESSAGE.json()
    ALTERNATE_MESSAGE = GeneralMessage(**ALTERNATE_JSON)
    TEST_TOPIC1 = "unit_test"
    TEST_TOPIC2 = "alternate"
    WAIT_TIME = 0.1  # should be enough to allow the messages to be received by the handler

    async def helper_equality_tester(self, callback_object: MessageCallback,
                                     expected_message: Union[BaseMessage, dict, str], expected_topic: str):
        """Helper function to test that the last recorded messages are equal to the expected ones."""
        # Wait a short time to allow the message to be received by the handler object.
        await asyncio.sleep(TestMessageCallback.WAIT_TIME)

        self.assertEqual(callback_object.last_message, expected_message)
        self.assertEqual(HANDLER.last_message, expected_message)

        self.assertEqual(callback_object.last_topic, expected_topic)
        self.assertEqual(HANDLER.last_topic, expected_topic)

    async def test_simulation_state_message(self):
        """Unit test for the callback handling simulation state messages."""
        callback_object = MessageCallback(HANDLER.message_handler, "SimState")

        state_message = SimulationStateMessage(**{
            **TestMessageCallback.GENERAL_JSON, MESSAGE_TYPE_ATTRIBUTE: "SimState"})
        alternate_message = SimulationStateMessage(**{**ALTERNATE_JSON, MESSAGE_TYPE_ATTRIBUTE: "SimState"})
        epoch_message = EpochMessage(**{**TestMessageCallback.GENERAL_JSON, MESSAGE_TYPE_ATTRIBUTE: "Epoch"})

        # test the simulation state callback with proper simulation state messages
        await callback_object.callback(
            get_incoming_message(state_message.bytes(), TestMessageCallback.TEST_TOPIC1))
        await self.helper_equality_tester(callback_object, state_message, TestMessageCallback.TEST_TOPIC1)

        await callback_object.callback(
            get_incoming_message(alternate_message.bytes(), TestMessageCallback.TEST_TOPIC2))
        await self.helper_equality_tester(callback_object, alternate_message, TestMessageCallback.TEST_TOPIC2)

        # test the simulation state callback with an epoch message => should be given as JSON object
        await callback_object.callback(
            get_incoming_message(epoch_message.bytes(), TestMessageCallback.TEST_TOPIC1))
        await self.helper_equality_tester(callback_object, epoch_message.json(), TestMessageCallback.TEST_TOPIC1)

    async def test_epoch_callback(self):
        """Unit test for the callback handling epoch messages."""
        callback_object = MessageCallback(HANDLER.message_handler, "Epoch")

        epoch_message = EpochMessage(**{**TestMessageCallback.GENERAL_JSON, MESSAGE_TYPE_ATTRIBUTE: "Epoch"})
        alternate_message = EpochMessage(**{**ALTERNATE_JSON, MESSAGE_TYPE_ATTRIBUTE: "Epoch"})
        state_message = SimulationStateMessage(**{
            **TestMessageCallback.GENERAL_JSON, MESSAGE_TYPE_ATTRIBUTE: "SimState"})

        # test the epoch callback with proper epoch messages
        await callback_object.callback(
            get_incoming_message(epoch_message.bytes(), TestMessageCallback.TEST_TOPIC1))
        await self.helper_equality_tester(callback_object, epoch_message, TestMessageCallback.TEST_TOPIC1)

        await callback_object.callback(
            get_incoming_message(alternate_message.bytes(), TestMessageCallback.TEST_TOPIC2))
        await self.helper_equality_tester(callback_object, alternate_message, TestMessageCallback.TEST_TOPIC2)

        # test the epoch callback with a simulation state message => should be given as JSON object
        await callback_object.callback(
            get_incoming_message(state_message.bytes(), TestMessageCallback.TEST_TOPIC1))
        await self.helper_equality_tester(callback_object, state_message.json(), TestMessageCallback.TEST_TOPIC1)

    async def test_status_message(self):
        """Unit test for the callback handling status messages."""
        callback_object = MessageCallback(HANDLER.message_handler, "Status")

        status_message = StatusMessage(**{**TestMessageCallback.GENERAL_JSON, MESSAGE_TYPE_ATTRIBUTE: "Status"})
        alternate_message = StatusMessage(**{**ALTERNATE_JSON, MESSAGE_TYPE_ATTRIBUTE: "Status"})
        state_message = SimulationStateMessage(**{
            **TestMessageCallback.GENERAL_JSON, MESSAGE_TYPE_ATTRIBUTE: "SimState"})

        # test the status callback with proper status messages
        await callback_object.callback(
            get_incoming_message(status_message.bytes(), TestMessageCallback.TEST_TOPIC1))
        await self.helper_equality_tester(callback_object, status_message, TestMessageCallback.TEST_TOPIC1)

        await callback_object.callback(
            get_incoming_message(alternate_message.bytes(), TestMessageCallback.TEST_TOPIC2))
        await self.helper_equality_tester(callback_object, alternate_message, TestMessageCallback.TEST_TOPIC2)

        # test the status callback with a simulation state message => should be given as JSON object
        await callback_object.callback(
            get_incoming_message(state_message.bytes(), TestMessageCallback.TEST_TOPIC1))
        await self.helper_equality_tester(callback_object, state_message.json(), TestMessageCallback.TEST_TOPIC1)

    async def test_resource_states_message(self):
        """Unit test for the callback handling status messages."""
        callback_object = MessageCallback(HANDLER.message_handler, "ResourceState")

        resource_states_message = ResourceStateMessage(**{
            **TestMessageCallback.GENERAL_JSON, MESSAGE_TYPE_ATTRIBUTE: "ResourceState"})
        alternate_message = ResourceStateMessage(**{**ALTERNATE_JSON, MESSAGE_TYPE_ATTRIBUTE: "ResourceState"})
        state_message = SimulationStateMessage(**{
            **TestMessageCallback.GENERAL_JSON, MESSAGE_TYPE_ATTRIBUTE: "SimState"})

        # test the status callback with proper resource states messages
        await callback_object.callback(
            get_incoming_message(resource_states_message.bytes(), TestMessageCallback.TEST_TOPIC1))
        await self.helper_equality_tester(callback_object, resource_states_message, TestMessageCallback.TEST_TOPIC1)

        await callback_object.callback(
            get_incoming_message(alternate_message.bytes(), TestMessageCallback.TEST_TOPIC2))
        await self.helper_equality_tester(callback_object, alternate_message, TestMessageCallback.TEST_TOPIC2)

        # test the status callback with a simulation state message => should be given as JSON object
        await callback_object.callback(
            get_incoming_message(state_message.bytes(), TestMessageCallback.TEST_TOPIC1))
        await self.helper_equality_tester(callback_object, state_message.json(), TestMessageCallback.TEST_TOPIC1)

    async def test_result_message(self):
        """Unit test for the callback handling general result messages."""
        callback_object = MessageCallback(HANDLER.message_handler, "Result")

        result_message = ResultMessage(**{**TestMessageCallback.GENERAL_JSON, MESSAGE_TYPE_ATTRIBUTE: "Result"})
        alternate_message = ResultMessage(**{**ALTERNATE_JSON, MESSAGE_TYPE_ATTRIBUTE: "Result"})
        state_message = SimulationStateMessage(**{
            **TestMessageCallback.GENERAL_JSON, MESSAGE_TYPE_ATTRIBUTE: "SimState"})

        # test the status callback with proper status messages
        await callback_object.callback(
            get_incoming_message(result_message.bytes(), TestMessageCallback.TEST_TOPIC1))
        await self.helper_equality_tester(callback_object, result_message, TestMessageCallback.TEST_TOPIC1)

        await callback_object.callback(
            get_incoming_message(alternate_message.bytes(), TestMessageCallback.TEST_TOPIC2))
        await self.helper_equality_tester(callback_object, alternate_message, TestMessageCallback.TEST_TOPIC2)

        # test the status callback with a simulation state message => should be given as JSON object
        await callback_object.callback(
            get_incoming_message(state_message.bytes(), TestMessageCallback.TEST_TOPIC1))
        await self.helper_equality_tester(callback_object, state_message.json(), TestMessageCallback.TEST_TOPIC1)

    async def test_general_message(self):
        """Unit test for the handling of a general simulation platform message."""
        callback_object = MessageCallback(HANDLER.message_handler)
        callback_object_general = MessageCallback(HANDLER.message_handler, "General")

        epoch_message = EpochMessage(**{**TestMessageCallback.GENERAL_JSON, MESSAGE_TYPE_ATTRIBUTE: "Epoch"})
        state_message = SimulationStateMessage(**{
            **TestMessageCallback.GENERAL_JSON, MESSAGE_TYPE_ATTRIBUTE: "SimState"})
        status_message = StatusMessage(**{**TestMessageCallback.GENERAL_JSON, MESSAGE_TYPE_ATTRIBUTE: "Status"})
        resource_states_message = ResourceStateMessage(**{
            **TestMessageCallback.GENERAL_JSON, MESSAGE_TYPE_ATTRIBUTE: "ResourceState"})
        result_message = ResultMessage(**{**TestMessageCallback.GENERAL_JSON, MESSAGE_TYPE_ATTRIBUTE: "Result"})
        general_message = GeneralMessage(**{**TestMessageCallback.GENERAL_JSON, MESSAGE_TYPE_ATTRIBUTE: "General"})

        # By default the test message should be a simulation state message because
        # DEFAULT_MESSAGE_TYPE == "SimState" as is defined in messages_common.py.
        await callback_object.callback(
            get_incoming_message(TestMessageCallback.GENERAL_MESSAGE.bytes(), TestMessageCallback.TEST_TOPIC1))
        await self.helper_equality_tester(
            callback_object, state_message, TestMessageCallback.TEST_TOPIC1)

        await callback_object_general.callback(
            get_incoming_message(TestMessageCallback.GENERAL_MESSAGE.bytes(), TestMessageCallback.TEST_TOPIC1))
        await self.helper_equality_tester(
            callback_object_general, TestMessageCallback.GENERAL_MESSAGE, TestMessageCallback.TEST_TOPIC1)

        await callback_object.callback(
            get_incoming_message(TestMessageCallback.ALTERNATE_MESSAGE.bytes(), TestMessageCallback.TEST_TOPIC2))
        await self.helper_equality_tester(
            callback_object, TestMessageCallback.ALTERNATE_MESSAGE, TestMessageCallback.TEST_TOPIC2)

        # Tests for the different message types.
        await callback_object.callback(
            get_incoming_message(epoch_message.bytes(), TestMessageCallback.TEST_TOPIC1))
        await self.helper_equality_tester(callback_object, epoch_message, TestMessageCallback.TEST_TOPIC1)

        await callback_object.callback(
            get_incoming_message(state_message.bytes(), TestMessageCallback.TEST_TOPIC2))
        await self.helper_equality_tester(callback_object, state_message, TestMessageCallback.TEST_TOPIC2)

        await callback_object.callback(
            get_incoming_message(status_message.bytes(), TestMessageCallback.TEST_TOPIC1))
        await self.helper_equality_tester(callback_object, status_message, TestMessageCallback.TEST_TOPIC1)

        await callback_object.callback(
            get_incoming_message(resource_states_message.bytes(), TestMessageCallback.TEST_TOPIC2))
        await self.helper_equality_tester(callback_object, resource_states_message, TestMessageCallback.TEST_TOPIC2)

        await callback_object.callback(
            get_incoming_message(result_message.bytes(), TestMessageCallback.TEST_TOPIC1))
        await self.helper_equality_tester(callback_object, result_message, TestMessageCallback.TEST_TOPIC1)

        await callback_object.callback(
            get_incoming_message(general_message.bytes(), TestMessageCallback.TEST_TOPIC1))
        await self.helper_equality_tester(callback_object, general_message, TestMessageCallback.TEST_TOPIC1)

        # Test for a JSON not conforming to the simulation platform message schema.
        await callback_object.callback(
            get_incoming_message(bytes(json.dumps(FAIL_TEST_JSON), encoding="UTF-8"), TestMessageCallback.TEST_TOPIC2))
        await self.helper_equality_tester(callback_object, FAIL_TEST_JSON, TestMessageCallback.TEST_TOPIC2)

        # Test for a non-JSON message.
        await callback_object.callback(
            get_incoming_message(bytes(FAIL_TEST_STR, encoding="UTF-8"), TestMessageCallback.TEST_TOPIC1))
        await self.helper_equality_tester(callback_object, FAIL_TEST_STR, TestMessageCallback.TEST_TOPIC1)
