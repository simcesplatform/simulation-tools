# -*- coding: utf-8 -*-

"""Unit test module for the AbstractSimulationComponent class."""

import asyncio
import datetime
from typing import List, Union, cast

import aiounittest

from tools.clients import RabbitmqClient
from tools.components import AbstractSimulationComponent
from tools.datetime_tools import to_iso_format_datetime_string
from tools.messages import AbstractMessage, EpochMessage, ErrorMessage, SimulationStateMessage, StatusMessage, \
                           get_next_message_id
from tools.tools import EnvironmentVariable


async def send_message(message_client: RabbitmqClient, message_object: AbstractMessage) -> None:
    """Sends the given message to the message bus using the given message client."""
    topic_name = message_object.message_type
    await message_client.send_message(topic_name, message_object.bytes())


class MessageStorage:
    """Helper class for storing received messages through callback function."""
    def __init__(self, ignore_source_process_id: str):
        self.messages = []
        self.ignore_source_process_id = ignore_source_process_id

    async def callback(self, message_object: Union[AbstractMessage, dict, str], message_topic: str) -> None:
        """Adds the given message and topic to the messages list."""
        if not isinstance(message_object, AbstractMessage):
            raise ValueError(message_object)
        if message_object.source_process_id != self.ignore_source_process_id:
            self.messages.append((message_object, message_topic))


class MessageGenerator:
    """Message generator for unit tests."""
    def __init__(self, simulation_id: str, process_id: str):
        self.simulation_id = simulation_id
        self.process_id = process_id
        self.id_generator = get_next_message_id(self.process_id)
        self.initial_time = datetime.datetime(2020, 1, 1, 0, 0, 0, 0, tzinfo=datetime.timezone.utc)
        self.epoch_interval = 3600
        self.latest_message_id = "-".join([process_id, "0"])

    def get_simulation_state_message(self, is_running: bool) -> SimulationStateMessage:
        """Returns a simulation state message."""
        self.latest_message_id = next(self.id_generator)
        return SimulationStateMessage(**{
            "Type": "SimState",
            "SimulationId": self.simulation_id,
            "SourceProcessId": self.process_id,
            "MessageId": self.latest_message_id,
            "SimulationState": "running" if is_running else "stopped"
        })

    def get_epoch_message(self, epoch_number: int, triggering_message_ids: List[str]) -> EpochMessage:
        """Returns an epoch messages."""
        self.latest_message_id = next(self.id_generator)
        return EpochMessage(**{
            "Type": "Epoch",
            "SimulationId": self.simulation_id,
            "SourceProcessId": self.process_id,
            "MessageId": self.latest_message_id,
            "EpochNumber": epoch_number,
            "TriggeringMessageIds": triggering_message_ids,
            "StartTime": to_iso_format_datetime_string(
                self.initial_time + (epoch_number - 1) * datetime.timedelta(seconds=self.epoch_interval)),
            "EndTime": to_iso_format_datetime_string(
                self.initial_time + epoch_number * datetime.timedelta(seconds=self.epoch_interval))
        })

    def get_status_message(self, epoch_number: int, triggering_message_ids: List[str]) -> StatusMessage:
        """Returns a status message."""
        self.latest_message_id = next(self.id_generator)
        return StatusMessage(**{
            "Type": "Status",
            "SimulationId": self.simulation_id,
            "SourceProcessId": self.process_id,
            "MessageId": self.latest_message_id,
            "EpochNumber": epoch_number,
            "TriggeringMessageIds": triggering_message_ids,
            "Value": "ready"
        })

    def get_error_message(self, epoch_number: int, triggering_message_ids: List[str], description: str) -> ErrorMessage:
        """Returns an error message."""
        self.latest_message_id = next(self.id_generator)
        return ErrorMessage(**{
            "Type": "Status",
            "SimulationId": self.simulation_id,
            "SourceProcessId": self.process_id,
            "MessageId": self.latest_message_id,
            "EpochNumber": epoch_number,
            "TriggeringMessageIds": triggering_message_ids,
            "Description": description
        })


class TestAbstractSimulationComponent(aiounittest.AsyncTestCase):
    """Unit tests for sending and receiving messages using AbstractSimulationComponent object."""
    simulation_id = cast(str, EnvironmentVariable("SIMULATION_ID", str).value)
    component_name = cast(str, EnvironmentVariable("SIMULATION_COMPONENT_NAME", str).value)
    short_wait = 0.5
    long_wait = 5.0

    async def epoch_tester(self, epoch_number: int, message_client: RabbitmqClient, message_storage: MessageStorage,
                           manager_message_generator: MessageGenerator, component_message_generator: MessageGenerator):
        """Test the behaviour of the test_component in one epoch."""
        number_of_previous_messages = len(message_storage.messages)
        if epoch_number == 0:
            manager_message = manager_message_generator.get_simulation_state_message(True)
        else:
            manager_message = manager_message_generator.get_epoch_message(
                epoch_number, [component_message_generator.latest_message_id])
        expected_respond = component_message_generator.get_status_message(epoch_number, [manager_message.message_id])

        await send_message(message_client, manager_message)
        # Wait a short time to allow the message storage to store the respond.
        await asyncio.sleep(TestAbstractSimulationComponent.short_wait)

        received_messages = message_storage.messages
        self.assertEqual(len(received_messages), number_of_previous_messages + 1)

        received_message, received_topic = received_messages[-1]
        self.assertEqual(received_topic, "Status")
        self.assertIsInstance(received_message, StatusMessage)
        self.assertEqual(received_message.message_type, expected_respond.message_type)
        self.assertEqual(received_message.simulation_id, expected_respond.simulation_id)
        self.assertEqual(received_message.source_process_id, expected_respond.source_process_id)
        self.assertEqual(received_message.epoch_number, expected_respond.epoch_number)
        self.assertEqual(received_message.triggering_message_ids, expected_respond.triggering_message_ids)
        self.assertEqual(received_message.value, expected_respond.value)
        # The id number in the message id does not have to be exactly the exprected but check the starting string.
        self.assertEqual("-".join(received_message.message_id.split("-")[:-1]),
                         "-".join(expected_respond.message_id.split("-")[:-1]))

    async def test_normal_simulation(self):
        """A test with a normal input in a simulation containing only manager and test component."""
        test_manager_name = "test_manager"
        manager_message_generator = MessageGenerator(TestAbstractSimulationComponent.simulation_id, test_manager_name)
        component_message_generator = MessageGenerator(TestAbstractSimulationComponent.simulation_id,
                                                       TestAbstractSimulationComponent.component_name)
        message_storage = MessageStorage(test_manager_name)

        test_client = RabbitmqClient()
        test_client.add_listener("#", message_storage.callback)
        test_component = AbstractSimulationComponent()
        await test_component.start()

        # Wait for a few seconds to allow the component to setup.
        await asyncio.sleep(TestAbstractSimulationComponent.long_wait)
        self.assertFalse(test_component.is_stopped)
        self.assertFalse(test_component.is_client_closed)
        self.assertFalse(test_client.is_closed)

        for epoch_number in range(0, 11):
            await self.epoch_tester(epoch_number, test_client, message_storage,
                                    manager_message_generator, component_message_generator)

        end_message = manager_message_generator.get_simulation_state_message(False)
        await send_message(test_client, end_message)
        await test_client.close()

        # Wait a few seconds to allow the test component and the message clients to close.
        await asyncio.sleep(TestAbstractSimulationComponent.long_wait)

        self.assertTrue(test_component.is_stopped)
        self.assertTrue(test_component.is_client_closed)
        self.assertTrue(test_client.is_closed)

    async def test_error_message(self):
        """Unit test for simulation component sending an error message."""
        # TODO: implement test_error_message

    async def test_component_robustness(self):
        """Unit test for testing simulation component behaviour when simulation does not go smoothly."""
        # TODO: implement test_component_robustness
