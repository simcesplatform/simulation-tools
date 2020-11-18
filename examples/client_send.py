# -*- coding: utf-8 -*-

"""This module contains code examples related to using the message classes."""

import asyncio

from examples.client import get_client
from tools.messages import MessageGenerator


def send_message(client, topic_name, message_bytes):
    """Sends a message to the message bus."""
    asyncio.create_task(client.send_message(topic_name, message_bytes))


async def start_sender():
    """Starts the test sender."""
    client = get_client()
    generator = MessageGenerator("2000-01-01T12:00:00.000Z", "TestProcess")

    print()
    message = generator.get_epoch_message(
        EpochNumber=1,
        TriggeringMessageIds=["message-id"],
        StartTime="2020-01-01T00:00:00.000Z",
        EndTime="2020-01-01T01:00:00.000Z")
    await client.send_message("Epoch", message.bytes())

    await asyncio.sleep(5)
    print()

    message = generator.get_status_ready_message(
        EpochNumber=1,
        TriggeringMessageIds=["message-id-2"])
    await client.send_message("Status", message.bytes())

    await asyncio.sleep(5)
    print()

    message = generator.get_status_ready_message(
        EpochNumber=1,
        TriggeringMessageIds=["message-id-3"])
    await client.send_message("Status", message.bytes())

    await asyncio.sleep(5)
    print()

    message = generator.get_status_ready_message(
        EpochNumber=2,
        TriggeringMessageIds=["new-id", "new-id2"])
    send_message(client, "Status", message.bytes())

    await asyncio.sleep(5)
    print()

    message = generator.get_simulation_state_message(SimulationState="stopped")
    send_message(client, "SimState", message.bytes())

    await asyncio.sleep(5)
    await client.close()


if __name__ == '__main__':
    asyncio.run(start_sender())
