# -*- coding: utf-8 -*-

"""This module contains code examples related to using the message classes."""

import asyncio
from typing import Union

from examples.client import get_client
from tools.messages import BaseMessage, AbstractMessage


class MessageReceiver:
    """Simple class for recording received messages."""
    def __init__(self):
        self.count = 0

    async def callback(self, message_object: Union[BaseMessage, dict, str], topic_name: str):
        """Method that can be used to receive message from RabbitMQ message bus."""
        self.count += 1
        if isinstance(message_object, AbstractMessage):
            message_type = message_object.message_type
        elif isinstance(message_object, dict):
            message_type = message_object.get("Type", "Unknown")
        else:
            message_type = "Unknown"

        print()
        print("Received '{:s}' message from topic '{:s}'".format(message_type, topic_name))
        print("Full message:", message_object)
        print()
        print("Total of {:d} message received".format(self.count))


async def start_receiver():
    """Starts the message receiver."""
    client = get_client()
    message_receiver = MessageReceiver()
    client.add_listener("#", message_receiver.callback)

    while message_receiver.count < 10:
        await asyncio.sleep(5)

    await client.close()


if __name__ == '__main__':
    asyncio.run(start_receiver())
