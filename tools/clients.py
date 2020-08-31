# -*- coding: utf-8 -*-

"""This module contains a class for keeping track of the simulation components."""

import asyncio

import aio_pika

from tools.callbacks import MessageCallback
from tools.messages import AbstractMessage
from tools.tools import FullLogger, handle_async_exception, load_environmental_variables

LOGGER = FullLogger(__name__)


def default_env_variable_definitions():
    """Returns the default environment variable definitions."""
    def env_variable_name(simple_variable_name):
        return "{:s}{:s}".format(RabbitmqClient.DEFAULT_ENV_VARIABLE_PREFIX, simple_variable_name.upper())

    return [
        (env_variable_name("host"), str, "localhost"),
        (env_variable_name("port"), int, 5672),
        (env_variable_name("login"), str, ""),
        (env_variable_name("password"), str, ""),
        (env_variable_name("ssl"), bool, False),
        (env_variable_name("ssl_version"), str, "PROTOCOL_TLS"),
        (env_variable_name("exchange"), str, "")
    ]


def load_config_from_env_variables():
    """Returns configuration dictionary from which values are fetched from environmental variables."""
    def simple_name(env_variable_name):
        return env_variable_name[len(RabbitmqClient.DEFAULT_ENV_VARIABLE_PREFIX):].lower()

    env_variables = load_environmental_variables(*default_env_variable_definitions())

    return {
        simple_name(variable_name): env_variables[variable_name]
        for variable_name in env_variables
    }


def validate_message(topic_name, message_to_publish):
    """Validates the message received from a queue for publishing.
       Returns a tuple (topic_name: str, message_to_publish: bytes) if the message is valid.
       Otherwise, returns (None, None)."""
    if not isinstance(topic_name, str):
        topic_name = str(topic_name)
    if isinstance(message_to_publish, AbstractMessage):
        message_to_publish = message_to_publish.bytes()

    if topic_name == "":
        LOGGER.warning("Topic name for the message to publish was empty.")
        return None, None

    if not isinstance(message_to_publish, bytes):
        LOGGER.warning("Wrong message type ('{:s}') for publishing.".format(str(type(message_to_publish))))
        return None, None

    return topic_name, message_to_publish


class RabbitmqConnection:
    """Class for holding a RabbitMQ connection including the a channel and an exchange."""
    def __init__(self, connection_parameters, exchange_name):
        self.__connection_parameters = connection_parameters
        self.__exchange_name = exchange_name

        self.__rabbitmq_connection = None
        self.__rabbitmq_channel = None
        self.__rabbitmq_exchange = None

    async def get_connection(self):
        """Returns a RabbitMQ connection. Creates the connection on the first call.
           If the connection has been closed, tries to create a new connection."""
        if self.__rabbitmq_connection is None or self.__rabbitmq_connection.is_closed:
            self.__rabbitmq_connection = await aio_pika.connect_robust(**self.__connection_parameters)
            self.__rabbitmq_channel = None
            self.__rabbitmq_exchange = None
        return self.__rabbitmq_connection

    async def get_channel(self):
        """Returns a channel for a RabbitMQ connection. Creates the channel on the first call."""
        if self.__rabbitmq_channel is None or self.__rabbitmq_channel.is_closed:
            connection = await self.get_connection()
            self.__rabbitmq_channel = await connection.channel()
            self.__rabbitmq_exchange = None
        return self.__rabbitmq_channel

    async def get_exchange(self):
        """Returns an exchange for a RabbitMQ connection. Declares the exchange on the first call."""
        if self.__rabbitmq_exchange is None:
            channel = await self.get_channel()
            self.__rabbitmq_exchange = await channel.declare_exchange(
                self.__exchange_name,
                aio_pika.exchange.ExchangeType.TOPIC,
                durable=True)
        return self.__rabbitmq_exchange

    async def close(self):
        """Closes the RabbitMQ connection."""
        if self.__rabbitmq_connection is not None and not self.__rabbitmq_connection.is_closed:
            await self.__rabbitmq_connection.close()

        self.__rabbitmq_connection = None
        self.__rabbitmq_channel = None
        self.__rabbitmq_exchange = None


class RabbitmqClient:
    """RabbitMQ client that can be used to send messages and to create topic listeners."""
    DEFAULT_ENV_VARIABLE_PREFIX = "RABBITMQ_"
    CONNECTION_PARAMTERS = ["host", "port", "login", "password", "ssl"]
    OPTIONAL_SSL_PARAMETER_TOP = "ssl_options"
    OPTIONAL_SSL_PARAMETER = "ssl_version"

    EXCHANGE_ATTRIBUTE_NAME = "exchange"

    MESSAGE_ENCODING = "UTF-8"

    def __init__(self, **kwargs):
        if not kwargs:
            kwargs = load_config_from_env_variables()

        self.__connection_parameters = RabbitmqClient.__get_connection_parameters_only(kwargs)
        self.__exchange_name = kwargs[RabbitmqClient.EXCHANGE_ATTRIBUTE_NAME]

        self.__send_connection = RabbitmqConnection(self.__connection_parameters, self.__exchange_name)
        self.__listened_topics = set()
        self.__listener_connections = []
        self.__listener_tasks = []

        self.__lock = asyncio.Lock()
        self.__is_closed = False

    async def close(self):
        """Closes the sender thread and all the listener threads."""
        async with self.__lock:
            await self.remove_listeners()
            await self.__send_connection.close()
            self.__is_closed = True

    @property
    def is_closed(self):
        """Returns True if the connections for the client have been closed."""
        return self.__is_closed

    @property
    def exchange_name(self):
        """Returns the RabbitMQ exchange name that the client uses."""
        return self.__exchange_name

    @property
    def listened_topics(self):
        """Returns a list of the topics the client is currently listening."""
        return list(self.__listened_topics)

    def add_listener(self, topic_names, callback_function):
        """Adds a new listener to the given topic."""
        if self.is_closed:
            return

        if isinstance(topic_names, str):
            topic_names = [topic_names]

        new_connection = RabbitmqConnection(self.__connection_parameters, self.__exchange_name)
        asyncio.get_event_loop().set_exception_handler(handle_async_exception)
        listener_task = asyncio.create_task(self.__listen_to_topics(
            connection_class=new_connection,
            topic_names=topic_names,
            callback_class=MessageCallback(callback_function)
        ))

        self.__listener_connections.append(new_connection)
        self.__listener_tasks.append(listener_task)
        for topic_name in topic_names:
            self.__listened_topics.add(topic_name)

    async def remove_listeners(self):
        """Removes all listeners from the client."""
        for listener_connection, listener_task in zip(self.__listener_connections, self.__listener_tasks):
            listener_task.cancel()
            await listener_connection.close()

        self.__listener_connections = []
        self.__listener_tasks = []
        self.__listened_topics = set()

    async def send_message(self, topic_name, message_bytes):
        """Sends the given message to the given topic. Assumes that the message is in bytes format."""
        async with self.__lock:
            if self.is_closed:
                LOGGER.warning("Message not sent because the client is closed.")
                return

            topic_name, message_to_publish = validate_message(topic_name, message_bytes)
            if topic_name is None or message_to_publish is None:
                return

            try:
                send_exchange = await self.__send_connection.get_exchange()
                await send_exchange.publish(aio_pika.Message(message_to_publish), routing_key=topic_name)
                LOGGER.debug("Message '{:s}' send to topic: '{:s}'".format(
                    message_to_publish.decode(RabbitmqClient.MESSAGE_ENCODING), topic_name))

            except SystemExit:
                LOGGER.debug("SystemExit received when trying to publish message.")
                await self.__send_connection.close()
                raise
            except RuntimeError as error:
                LOGGER.warning("RunTimeError: '{:s}' when trying to publish message.".format(str(error)))
            except OSError as error:
                LOGGER.warning("OSError: '{:s}' when trying to publish message.".format(str(error)))
            except GeneratorExit:
                LOGGER.warning("GeneratorExit received when trying to publish message.")

    async def __listen_to_topics(self, connection_class, topic_names, callback_class):
        """Starts a RabbitMQ message bus listener for the given topics."""
        if isinstance(topic_names, str):
            topic_names = [topic_names]
        LOGGER.info("Opening RabbitMQ listener for the topics: '{:s}'".format(", ".join(topic_names)))

        try:
            rabbitmq_connection = await connection_class.get_connection()

            async with rabbitmq_connection:
                rabbitmq_channel = await connection_class.get_channel()
                rabbitmq_queue = await rabbitmq_channel.declare_queue(
                    auto_delete=True,  # Delete the queue when no one uses it anymore
                    exclusive=True     # No other application can access the queue; delete on exit
                )
                rabbitmq_exchange = await connection_class.get_exchange()

                # Binding the queue to the given topics
                for topic_name in topic_names:
                    # await rabbitmq_queue.bind(rabbitmq_exchange, routing_key=topic_name)
                    await rabbitmq_queue.bind(rabbitmq_exchange, routing_key=topic_name)
                    LOGGER.info("Now listening to messages; exc={:s}, topic={:s}".format(
                        rabbitmq_exchange.name, topic_name))

                async with rabbitmq_queue.iterator() as queue_iter:
                    async for message in queue_iter:
                        async with message.process():
                            LOGGER.debug("Message '{:s}' received from topic: '{:s}'".format(
                                message.body.decode(RabbitmqClient.MESSAGE_ENCODING), message.routing_key))
                            await callback_class.callback(message)

        except SystemExit:
            LOGGER.debug("SystemExit received when trying to listen to the message bus.")
            await connection_class.close()
            raise
        except RuntimeError as error:
            LOGGER.warning("RuntimeError: '{:s}' when trying to listen to the message bus.".format(str(error)))
        except OSError as error:
            LOGGER.warning("OSError: '{:s}' when trying to listen to the message bus.".format(str(error)))

    @classmethod
    def __get_connection_parameters_only(cls, connection_config_dict):
        """Returns only the parameters needed for creating a connection."""
        stripped_connection_config = {
            config_parameter: parameter_value
            for config_parameter, parameter_value in connection_config_dict.items()
            if config_parameter in cls.CONNECTION_PARAMTERS
        }
        if stripped_connection_config["ssl"]:
            stripped_connection_config[cls.OPTIONAL_SSL_PARAMETER_TOP] = {
                cls.OPTIONAL_SSL_PARAMETER: connection_config_dict[cls.OPTIONAL_SSL_PARAMETER]
            }

        return stripped_connection_config
