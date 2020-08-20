# -*- coding: utf-8 -*-

"""This module contains a class for writing and reading documents to a Mongo database."""

import pymongo

from tools.datetime_tools import to_utc_datetime_object
from tools.tools import FullLogger, load_environmental_variables

LOGGER = FullLogger(__name__)


def default_env_variable_definitions():
    """Returns the default environment variable definitions."""
    def env_variable_name(simple_variable_name):
        return "{:s}{:s}".format(MongodbClient.DEFAULT_ENV_VARIABLE_PREFIX, simple_variable_name.upper())

    return [
        (env_variable_name("host"), str, "localhost"),
        (env_variable_name("port"), int, 5672),
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
    DATETIME_ATTRIBUTES = ["Timestamp", "StartTime", "EndTime"]

    def __init__(self, **kwargs):
        if not kwargs:
            kwargs = load_config_from_env_variables()
        self.__connection_parameters = MongodbClient.__get_connection_parameters_only(kwargs)
        self.__database_name = kwargs["database"]
        self.__metadata_collection = kwargs["metadata_collection"]
        self.__messages_collection_prefix = kwargs["messages_collection_prefix"]
        self.__collection_identifier = kwargs["collection_identifier"]

        self.__mongo_client = pymongo.MongoClient(**self.__connection_parameters)
        self.__mongo_database = self.__mongo_client[self.__database_name]

    def store_message(self, json_document: dict, document_topic=None):
        """Stores a new JSON message to the database. The used collection is """
        if isinstance(document_topic, str):
            # Adds or replaces the topic attribute in the given JSON document with the parameter document_topic.
            json_document[MongodbClient.TOPIC_ATTRIBUTE] = document_topic

        message_collection_name = self.__get_message_collection(json_document)
        if message_collection_name is None:
            LOGGER.warning("Document does not have '{:s}' attribute.".format(self.__collection_identifier))
            return None

        # Convert the selected attributes from type str to datetime.datetime
        for datetime_attribute in MongodbClient.DATETIME_ATTRIBUTES:
            if datetime_attribute in json_document and isinstance(json_document[datetime_attribute], str):
                json_document[datetime_attribute] = to_utc_datetime_object(json_document[datetime_attribute])

        # TODO: update metadata collection if necessary

        mongodb_collection = self.__mongo_database[message_collection_name]
        write_result = mongodb_collection.insert_one(json_document)
        return write_result

    def __get_message_collection(self, json_document: dict):
        """Returns the collection name for the document."""
        if self.__collection_identifier not in json_document:
            return None
        return self.__messages_collection_prefix + json_document[self.__collection_identifier]

    @classmethod
    def __get_connection_parameters_only(cls, connection_config_dict):
        """Returns only the parameters needed for creating a connection."""
        stripped_connection_config = {
            config_parameter: parameter_value
            for config_parameter, parameter_value in connection_config_dict.items()
            if config_parameter in cls.CONNECTION_PARAMTERS
        }

        return stripped_connection_config
