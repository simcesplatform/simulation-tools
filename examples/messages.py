# -*- coding: utf-8 -*-

"""This module contains code examples related to using the message classes."""

import json
import logging

# the used message examples are defined in examples/message_json.py
from examples.message_json import status_ready_message, status_error_message, \
                                  invalid_status_1, invalid_status_2, invalid_status_3
from tools.exceptions.messages import MessageError
from tools.messages import StatusMessage, MessageGenerator
from tools.tools import FullLogger

# use the FullLogger for logging to show the output on the screen as well as to store it to a file
# the default file name for the log output is logfile.out
# the file name can be changed by using the environment variable SIMULATION_LOG_FILE
# in python code that can be done by:
#     import os
#     os.environ["SIMULATION_LOG_FILE"] = "my_logs.txt"
LOGGER = FullLogger(__name__, logger_level=logging.INFO)


def test_from_json():
    """Tests for creating message objects using from_json method."""
    LOGGER.info("Example of creating a Status ready message from JSON")
    status_ready = StatusMessage.from_json(status_ready_message)
    LOGGER.info("Status ready:   {}".format(type(status_ready)))
    LOGGER.info(json.dumps(status_ready.json(), indent=4))  # output the message as JSON in a readable format
    LOGGER.info("")

    # print out the attributes individually from the Status message
    # NOTE: that the JSON attribute names use Pascal case (e.g. MessageId) as is defined in the wiki
    #       while the message properties use snake case (e.g. message_id) as is usual in Python variables
    LOGGER.info("Type for Status message:                 {}".format(status_ready.message_type))
    LOGGER.info("SourceProcessId for Status message:      {}".format(status_ready.source_process_id))
    LOGGER.info("MessageId for Status message:            {}".format(status_ready.message_id))
    LOGGER.info("Timestamp for Status message:            {}".format(status_ready.timestamp))
    LOGGER.info("EpochNumber for Status message:          {}".format(status_ready.epoch_number))
    LOGGER.info("TriggeringMessageIds for Status message: {}".format(status_ready.triggering_message_ids))
    LOGGER.info("Value for Status message:                {}".format(status_ready.value))
    # the optional attributes will have value None if they have not been explicitly given
    LOGGER.info("LastUpdatedInEpoch for Status message:   {}".format(status_ready.last_updated_in_epoch))
    LOGGER.info("Warnings for Status message:             {}".format(status_ready.warnings))
    LOGGER.info("Descriptions for Status message:         {}".format(status_ready.description))
    LOGGER.info("")

    LOGGER.info("Example of creating a Status error message from JSON")
    status_error = StatusMessage.from_json(status_error_message)
    LOGGER.info("Status error:   {}".format(type(status_error)))
    LOGGER.info(json.dumps(status_ready.json(), indent=4))  # output the message as JSON in a readable format
    LOGGER.info("")

    LOGGER.info("Type for Status message:                 {}".format(status_error.message_type))
    LOGGER.info("SourceProcessId for Status message:      {}".format(status_error.source_process_id))
    LOGGER.info("MessageId for Status message:            {}".format(status_error.message_id))
    LOGGER.info("Timestamp for Status message:            {}".format(status_error.timestamp))
    LOGGER.info("EpochNumber for Status message:          {}".format(status_error.epoch_number))
    LOGGER.info("LastUpdatedInEpoch for Status message:   {}".format(status_error.last_updated_in_epoch))
    LOGGER.info("TriggeringMessageIds for Status message: {}".format(status_error.triggering_message_ids))
    LOGGER.info("Warnings for Status message:             {}".format(status_error.warnings))
    LOGGER.info("Value for Status message:                {}".format(status_error.value))
    LOGGER.info("Descriptions for Status message:         {}".format(status_error.description))
    LOGGER.info("")


def test_invalid_status():
    """Tests for trying to create status message instances with invalid values."""
    LOGGER.info("")
    # from_json method returns None if there is invalid values from some of the attributes
    invalid1 = StatusMessage.from_json(invalid_status_1)  # the Value attribute is missing
    LOGGER.info("{} : {}".format(type(invalid1), invalid1))
    LOGGER.info("")
    invalid2 = StatusMessage.from_json(invalid_status_2)  # the Value attribute has an invalid value
    LOGGER.info("{} : {}".format(type(invalid2), invalid2))
    LOGGER.info("")
    invalid3 = StatusMessage.from_json(invalid_status_3)  # the EpochNumber attribute has an invalid value
    LOGGER.info("{} : {}".format(type(invalid3), invalid3))
    LOGGER.info("")

    # Note:     StatusMessage(**{"attr1": value1, "attr2": value2})
    # is the as StatusMessage(attr1=value1, attr2=value)
    try:
        # using the constructor directly throws an exception when there is invalid attribute values
        invalid1 = StatusMessage(**invalid_status_1)
        LOGGER.info(str(invalid1))
    except MessageError as message_error:
        LOGGER.warning("Received an exception {}: {}".format(type(message_error), message_error))

    try:
        invalid2 = StatusMessage(**invalid_status_2)
        LOGGER.info(str(invalid2))
    except MessageError as message_error:
        LOGGER.warning("Received an exception {}: {}".format(type(message_error), message_error))

    try:
        invalid3 = StatusMessage(**invalid_status_3)
        LOGGER.info(str(invalid3))
    except MessageError as message_error:
        LOGGER.warning("Received an exception {}: {}".format(type(message_error), message_error))


def test_message_generator():
    """Examples for using the message generator class to help creating message objects."""
    LOGGER.info("")
    # The message generator takes the simulation id and the source process id as parameters
    # since they remain the same throughout the entire simulation run.
    message_generator = MessageGenerator(
        simulation_id="2020-11-01T00:00:00.000Z",
        source_process_id="Storage")

    # Using the general get_message method to create a Status ready message.
    LOGGER.info("Generating the first status message")
    status1 = message_generator.get_message(
        StatusMessage,
        EpochNumber=0,
        TriggeringMessageIds=["manager-1"],
        Value="ready")
    LOGGER.info("{} : {}".format(type(status1), status1))
    LOGGER.info("")

    # Using the direct helper method get_status_ready_message to create a Status ready message
    LOGGER.info("Generating the second status message")
    status2 = message_generator.get_status_ready_message(
        EpochNumber=1,
        TriggeringMessageIds=["manager-2"])
    LOGGER.info("{} : {}".format(type(status2), status2))
    LOGGER.info("")

    # Examples of trying to create an invalid status messages
    try:
        LOGGER.info("Trying to create a status message with missing triggering message ids")
        invalid1 = message_generator.get_message(
            StatusMessage,
            EpochNumber=12,
            Value="ready"
        )
        LOGGER.info(str(invalid1))
    except (TypeError, MessageError) as message_error:
        LOGGER.warning("Received an exception {}: {}".format(type(message_error), message_error))
    LOGGER.info("")

    try:
        LOGGER.info("Trying to create a status message with invalid value for epoch number")
        invalid2 = message_generator.get_status_ready_message(
            EpochNumber=-1,
            TriggeringMessageIds=[]
        )
        LOGGER.info(str(invalid2))
    except MessageError as message_error:
        LOGGER.warning("Received an exception {}: {}".format(type(message_error), message_error))
    LOGGER.info("")
