# -*- coding: utf-8 -*-

"""Unit tests for the RabbitmqClient class."""

import asyncio

import aiounittest

from tools.clients import RabbitmqClient
from tools.messages import EpochMessage, ErrorMessage, GeneralMessage, StatusMessage, get_next_message_id
from tools.tests.messages_common import EPOCH_TEST_JSON, ERROR_TEST_JSON, GENERAL_TEST_JSON, STATUS_TEST_JSON


def get_new_message(old_message, id_generator):
    """Returns a new message object with a new Timestamp and MessageId and
       other attributes equal to the old message"""
    json_message = old_message.json()
    json_message["MessageId"] = next(id_generator)
    json_message.pop("Timestamp")

    if isinstance(old_message, EpochMessage):
        return EpochMessage(**json_message)
    if isinstance(old_message, ErrorMessage):
        return ErrorMessage(**json_message)
    if isinstance(old_message, StatusMessage):
        return StatusMessage(**json_message)
    return GeneralMessage(**json_message)


class MessageStorage:
    """Helper class for storing received messages through callback function."""
    def __init__(self):
        self.messages = []

    async def callback(self, message_object, message_topic: str):
        """Adds the given message and topic to the messages list."""
        # print("here", self.messages, message_object.message_id)
        self.messages.append((message_object, message_topic))


class TestRabbitmqClient(aiounittest.AsyncTestCase):
    """Unit tests for sending and receiving messages using RabbitmqClient object."""
    async def test_message_sending_and_receiving(self):
        """Tests sending and receiving message using RabbitMQ message bus using RabbitmqClient.
           Checks that the correct messages are received and in the correct order."""
        # Setup the RabbitMQ clients.
        client1 = RabbitmqClient()
        client2 = RabbitmqClient()
        client3 = RabbitmqClient()
        client4 = RabbitmqClient()

        # Setup the message storage objects for the callback functions.
        message_storage1 = MessageStorage()
        message_storage2 = MessageStorage()
        message_storage3 = MessageStorage()
        message_storage4 = MessageStorage()

        # Setup the listeners for the clients.
        client1.add_listener(["TopicA.*", "TopicB.Error"], message_storage1.callback)
        client2.add_listener(["TopicA.Error", "TopicB.Epoch", "TopicB"], message_storage2.callback)
        client3.add_listener(["TopicA.Epoch", "TopicA.Status", "TopicB.#"], message_storage3.callback)
        client4.add_listener("#", message_storage4.callback)
        # 5 second wait to allow the listeners to setup
        await asyncio.sleep(5)

        # Setup the message id generators.
        id_generator1 = get_next_message_id("manager")
        id_generator2 = get_next_message_id("tester")
        id_generator3 = get_next_message_id("helper")

        # Load the base message objects.
        epoch_message = EpochMessage(**EPOCH_TEST_JSON)
        error_message = ErrorMessage(**ERROR_TEST_JSON)
        general_message = GeneralMessage(**GENERAL_TEST_JSON)
        status_message = StatusMessage(**STATUS_TEST_JSON)

        # Setup the check lists that are used to check whether the correct message were received.
        # At the end these should correspond to message_storage1.messages, message_storage2.messages, ...
        check_list1 = []
        check_list2 = []
        check_list3 = []
        check_list4 = []

        # Setup the test message schema. Each element contains the topic name, base message and
        # a list of the check lists that correspond to the lists that are expected to receive the messages.
        test_list = [
            ("TopicA", general_message, [check_list4]),
            ("TopicA.Epoch", epoch_message, [check_list1, check_list3, check_list4]),
            ("TopicA.Status", status_message, [check_list1, check_list3, check_list4]),
            ("TopicA.Error", error_message, [check_list1, check_list2, check_list4]),
            ("TopicA.Error.Special", error_message, [check_list4]),
            ("TopicB", general_message, [check_list2, check_list3, check_list4]),
            ("TopicB.Epoch", epoch_message, [check_list2, check_list3, check_list4]),
            ("TopicB.Status", status_message, [check_list3, check_list4]),
            ("TopicB.Error", error_message, [check_list1, check_list3, check_list4]),
            ("TopicB.Error.Special", error_message, [check_list3, check_list4]),
            ("TopicC", general_message, [check_list4])
        ]

        for send_client, message_id_generator in zip([client1, client2, client3],
                                                     [id_generator1, id_generator2, id_generator3]):
            for test_topic, test_message, check_lists in test_list:
                # Create a new message with a new timestamp and message id.
                new_test_message = get_new_message(test_message, message_id_generator)
                await send_client.send_message(test_topic, new_test_message.bytes())
                for check_list in check_lists:
                    check_list.append((new_test_message, test_topic))

        # 5 second wait to allow the message handlers to finish.
        await asyncio.sleep(5)

        # Check that the received messages equal to the excpected messages.
        self.assertEqual(message_storage1.messages, check_list1)
        self.assertEqual(message_storage2.messages, check_list2)
        self.assertEqual(message_storage3.messages, check_list3)
        self.assertEqual(message_storage4.messages, check_list4)

        # Close the clients.
        await client1.close()
        await client2.close()
        await client3.close()
        await client4.close()

        # 5 second wait to allow the clients to properly close.
        await asyncio.sleep(5)
