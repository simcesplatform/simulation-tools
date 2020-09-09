# -*- coding: utf-8 -*-

"""This module contains a class for writing and reading documents to a Mongo database."""

import datetime
import operator
from typing import List, Tuple, Union

import motor.motor_asyncio
import pymongo
import pymongo.results

from tools.datetime_tools import to_utc_datetime_object
from tools.tools import FullLogger, load_environmental_variables

LOGGER = FullLogger(__name__)


def default_env_variable_definitions():
    """Returns the default environment variable definitions."""
    def env_variable_name(simple_variable_name):
        return "{:s}{:s}".format(MongodbClient.DEFAULT_ENV_VARIABLE_PREFIX, simple_variable_name.upper())

    return [
        (env_variable_name("host"), str, "localhost"),
        (env_variable_name("port"), int, 27017),
        (env_variable_name("username"), str, ""),
        (env_variable_name("password"), str, ""),
        (env_variable_name("database"), str, "db"),
        (env_variable_name("appname"), str, "log_writer"),
        (env_variable_name("tz_aware"), bool, True),
        (env_variable_name("metadata_collection"), str, "simulations"),
        (env_variable_name("messages_collection_prefix"), str, "simulation_"),
        (env_variable_name("collection_identifier"), str, "SimulationId")
    ]


def load_config_from_env_variables():
    """Returns configuration dictionary from which values are fetched from environmental variables."""
    def simple_name(env_variable_name):
        return env_variable_name[len(MongodbClient.DEFAULT_ENV_VARIABLE_PREFIX):].lower()

    env_variables = load_environmental_variables(*default_env_variable_definitions())

    return {
        simple_name(variable_name): env_variables[variable_name]
        for variable_name in env_variables
    }


class MongodbClient:
    """MongoDB client that can be used to write JSON documents to Mongo database."""
    DEFAULT_ENV_VARIABLE_PREFIX = "MONGODB_"
    CONNECTION_PARAMTERS = ["host", "port", "username", "password", "appname", "tz_aware"]
    TOPIC_ATTRIBUTE = "Topic"

    # These attributes will be converted to datetime objects before writing to database.
    TIMESTAMP_ATTRIBUTE = "Timestamp"
    STARTTIME_ATTRIBUTE = "StartTime"
    ENDTIME_ATTRIBUTE = "EndTime"
    DATETIME_ATTRIBUTES = [
        TIMESTAMP_ATTRIBUTE,
        STARTTIME_ATTRIBUTE,
        ENDTIME_ATTRIBUTE
    ]

    # Additional attributes that are used in the collection indexes.
    EPOCH_ATTRIBUTE = "EpochNumber"
    PROCESS_ATTRIBUTE = "SourceProcessId"

    # List of possible metadata attributes in addition to the simulation id.
    # Each element is a tuple (attribute_name, attribute_types, comparison_operator)
    # attribute_types is 1-element list for non-list-attribute types and
    # n-element list for list-attribute types with the last element describing the internal type.
    # For attributes with comparison_operator is None, the previous value is always overwritten,
    # for other attributes, the previous value is overwritten only if old_value <comparison_operator> new_value.
    METADATA_ATTRIBUTES = [
        ("StartTime", [datetime.datetime], operator.gt),
        ("EndTime", [datetime.datetime], operator.lt),
        ("Name", [str], None),
        ("Description", [str], None),
        ("Epochs", [int], operator.lt),
        ("Processes", [list, str], None)
    ]

    def __init__(self, **kwargs):
        """Required attributes:
           - host                        : the host name for the MongoDB
           - port                        : the port number for the MongoDB
           - username                    : username for access to the MongoDB
           - password                    : password for access to the MongoDB
           - database                    : the database name used with the MongoDB
           - appname                     : application name for the connection to the MongoDB
           - tz_aware                    : are datetime values timezone aware (True/False)
           - metadata_collection         : the collection name for the simulation metadata
           - messages_collection_prefix  : the prefix for the collection names for the simulation messages
           - collection_identifier       : the attribute name in the messages that tells the simulation id

           If called without any parameters, the values for the attributes are read from the environmental variables
           - MONGODB_HOST (default value: "localhost")
           - MONGODB_PORT (default value: 27017)
           - MONGODB_USERNAME (default value: "")
           - MONGODB_PASSWORD (default value: "")
           - MONGODB_DATABASE (default value: "db")
           - MONGODB_APPNAME (default value: "log_writert")
           - MONGODB_TZ_AWARE (default value: True)
           - MONGODB_METADATA_COLLECTION (default value: "simulations")
           - MONGODB_MESSAGES_COLLECTION_PREFIX (default value: "simulation_")
           - MONGODB_COLLECTION_IDENTIFIER (default value: "SimulationId")
        """
        if not kwargs:
            kwargs = load_config_from_env_variables()
        self.__connection_parameters = MongodbClient.__get_connection_parameters_only(kwargs)
        self.__database_name = kwargs["database"]
        self.__metadata_collection_name = kwargs["metadata_collection"]
        self.__messages_collection_prefix = kwargs["messages_collection_prefix"]
        self.__collection_identifier = kwargs["collection_identifier"]

        # Set up the Mongo database connection and the metadata collection
        # self.__mongo_client = pymongo.MongoClient(**self.__connection_parameters)
        self.__mongo_client = motor.motor_asyncio.AsyncIOMotorClient(**self.__connection_parameters)
        self.__mongo_database = self.__mongo_client[self.__database_name]
        self.__metadata_collection = self.__mongo_database[self.__metadata_collection_name]

    @property
    def host(self) -> str:
        """The host name of the MongoDB."""
        return str(self.__connection_parameters["host"])

    @property
    def port(self) -> int:
        """The port number of the MongoDB."""
        return int(str(self.__connection_parameters["port"]))

    async def store_message(self, json_document: dict, document_topic=None) -> bool:
        """Stores a new JSON message to the database. The used collection is determined by
           the 'simulation_id' attribute in the message.
           Returns True, if writing to the database was successful.
        """
        if isinstance(document_topic, str):
            # Adds or replaces the topic attribute in the given JSON document with the parameter document_topic.
            json_document[MongodbClient.TOPIC_ATTRIBUTE] = document_topic

        message_collection_name = self.__get_message_collection(json_document)
        if message_collection_name is None:
            LOGGER.warning("Document does not have '{:s}' attribute.".format(self.__collection_identifier))
            return False

        await MongodbClient.datetime_attributes_to_objects(json_document)

        mongodb_collection = self.__mongo_database[message_collection_name]
        write_result = await mongodb_collection.insert_one(json_document)
        return write_result.acknowledged

    async def store_messages(self, documents: List[Tuple[dict, str]]):
        """Stores several messages to the database. All documents are expected to belong to the same simulation.
           The simulation is identified based on the first message on the list.

           documents parameters is expected to be a list of tuples (message_json, topic_name),
           where message_json is the message in JSON format and topic_name is a string for the message topic."""
        if not documents or not isinstance(documents, list):
            return []

        # Add the topic attribute to the JSON documents.
        full_documents = [
            {
                **document,
                MongodbClient.TOPIC_ATTRIBUTE: topic_name
            }
            for document, topic_name in documents
        ]

        message_collection_name = self.__get_message_collection(full_documents[0])
        if message_collection_name is None:
            LOGGER.warning("The first document does not have '{:s}' attribute.".format(self.__collection_identifier))
            return []

        await MongodbClient.datetime_attributes_to_objects(full_documents)

        mongodb_collection = self.__mongo_database[message_collection_name]
        write_result = await mongodb_collection.insert_many(full_documents)

        if write_result.acknowledged:
            return write_result.inserted_ids
        return []

    async def update_metadata(self, simulation_id: str, **attribute_updates):
        """Creates or updates the metadata information for a simulation."""
        if not isinstance(simulation_id, str):
            LOGGER.warning("Given simulation id was not of type str: '{:s}'".format(str(type(simulation_id))))
            return False

        simple_document = {self.__collection_identifier: simulation_id}
        metadata_document = await self.__metadata_collection.find_one(simple_document)

        # Add a new metadata document.
        if metadata_document is None:
            metadata_document = await self.get_metadata_json(simple_document, attribute_updates)
            write_result = await self.__metadata_collection.insert_one(metadata_document)
            return (
                isinstance(write_result, pymongo.results.InsertOneResult) and
                write_result.acknowledged
            )

        # Update previous document.
        metadata_document = await self.get_metadata_json(metadata_document, attribute_updates)
        write_result = await self.__metadata_collection.replace_one(simple_document, metadata_document)
        return (
            isinstance(write_result, pymongo.results.UpdateResult) and
            write_result.acknowledged and
            write_result.modified_count == 1
        )

    async def update_metadata_indexes(self):
        """Updates indexes to the metadata collection and adds them if they do not exist yet."""
        metadata_indexes = [
            pymongo.IndexModel(
                [(self.__collection_identifier, pymongo.ASCENDING)],
                name="simulation_id_index",
                unique=True
            ),
            pymongo.IndexModel(
                [
                    (MongodbClient.STARTTIME_ATTRIBUTE, pymongo.ASCENDING),
                    (MongodbClient.ENDTIME_ATTRIBUTE, pymongo.ASCENDING)
                ],
                name="start_time_index"
            ),
            pymongo.IndexModel(
                [(MongodbClient.ENDTIME_ATTRIBUTE, pymongo.ASCENDING)],
                name="end_time_index",
                sparse=True
            )
        ]

        result = await self.__metadata_collection.create_indexes(metadata_indexes)

        if len(result) != len(metadata_indexes):
            LOGGER.warning("Problem with updating metadata collection indexes, result: {:s}".format(str(result)))
        else:
            LOGGER.debug("Updated the metadata collection indexes successfully.")

    async def add_simulation_indexes(self, simulation_id: str):
        """Adds indexes to the collection containing the messages from the specified simulation."""
        simulation_indexes = [
            pymongo.IndexModel(
                [
                    (MongodbClient.EPOCH_ATTRIBUTE, pymongo.ASCENDING),
                    (MongodbClient.PROCESS_ATTRIBUTE, pymongo.ASCENDING),
                    (MongodbClient.TOPIC_ATTRIBUTE, pymongo.ASCENDING),
                ],
                name="epoch_index"
            ),
            pymongo.IndexModel(
                [
                    (MongodbClient.PROCESS_ATTRIBUTE, pymongo.ASCENDING),
                    (MongodbClient.TOPIC_ATTRIBUTE, pymongo.ASCENDING)
                ],
                name="process_index"
            ),
            pymongo.IndexModel(
                [
                    (MongodbClient.TOPIC_ATTRIBUTE, pymongo.ASCENDING),
                    (MongodbClient.STARTTIME_ATTRIBUTE, pymongo.ASCENDING)
                ],
                name="topic_index"
            )
        ]

        message_collection_name = self.__get_message_collection({self.__collection_identifier: simulation_id})
        result = await self.__mongo_database[message_collection_name].create_indexes(simulation_indexes)

        if len(result) != len(simulation_indexes):
            LOGGER.warning("Problem with updating message collection indexes for {:s}, result: {:s}".format(
                simulation_id, str(result)))
        else:
            LOGGER.debug("Updated the message collection indexes for {:s} successfully.".format(simulation_id))

    def __get_message_collection(self, json_document: dict):
        """Returns the collection name for the document."""
        if self.__collection_identifier not in json_document:
            return None
        return self.__messages_collection_prefix + json_document[self.__collection_identifier]

    @classmethod
    async def datetime_attributes_to_objects(cls, json_documents: Union[dict, list]):
        """Convert the datetime attributes from type str to datetime.datetime."""
        if not isinstance(json_documents, list):
            json_documents = [json_documents]

        for json_document in json_documents:
            for datetime_attribute in MongodbClient.DATETIME_ATTRIBUTES:
                if datetime_attribute in json_document and isinstance(json_document[datetime_attribute], str):
                    json_document[datetime_attribute] = to_utc_datetime_object(json_document[datetime_attribute])

    async def get_metadata_json(self, old_values: dict, new_values: dict):
        """Returns a validated metadata document. Any attributes that not
           simulation_id or in METADATA_ATTRIBUTES list are ignored."""
        if new_values is None:
            return None
        if old_values is None:
            old_values = {}

        simulation_id_old = old_values.get(self.__collection_identifier, None)
        simulation_id_new = new_values.get(self.__collection_identifier, None)
        if ((simulation_id_old is None and simulation_id_new is None) or
                (simulation_id_old is not None and simulation_id_new is not None and
                 simulation_id_old != simulation_id_new)):
            return None

        metadata_values = {self.__collection_identifier: simulation_id_old}
        for metadata_attribute in MongodbClient.METADATA_ATTRIBUTES:
            attribute_name, attribute_types, comparison_operator = metadata_attribute
            old_value = old_values.get(attribute_name, None)
            new_value = new_values.get(attribute_name, None)

            # New value is of proper type.
            if MongodbClient.__check_value_types(new_value, attribute_types):
                # Old value is of proper type.
                if MongodbClient.__check_value_types(old_value, attribute_types):
                    if comparison_operator is None or comparison_operator(old_value, new_value):
                        metadata_values[attribute_name] = new_value
                    else:
                        metadata_values[attribute_name] = old_value
                # Old value either does not exist is not of proper type.
                else:
                    metadata_values[attribute_name] = new_value
            # New value does not exist but the old value is usable.
            elif MongodbClient.__check_value_types(old_value, attribute_types):
                metadata_values[attribute_name] = old_value

        return metadata_values

    @classmethod
    def __check_value_types(cls, value, types: list):
        """Checks that value is of proper type. Used for the metadata attributes."""
        if value is None:
            return False
        if len(types) == 0:
            return True
        if len(types) == 1:
            return isinstance(value, types[0])

        try:
            for value_element in value:
                if not cls.__check_value_types(value_element, types[1:]):
                    return False
        except TypeError as error:
            LOGGER.warning("TypeError : {:s}".format(str(error)))
            return False

        return True

    @classmethod
    def __get_connection_parameters_only(cls, connection_config_dict):
        """Returns only the parameters needed for creating a connection."""
        stripped_connection_config = {
            config_parameter: parameter_value
            for config_parameter, parameter_value in connection_config_dict.items()
            if config_parameter in cls.CONNECTION_PARAMTERS
        }

        return stripped_connection_config
