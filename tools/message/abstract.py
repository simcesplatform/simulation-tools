# -*- coding: utf-8 -*-

"""This module contains the abstract base classes for the simulation platform messages."""

from __future__ import annotations
import datetime
import json
from typing import Any, Dict, List, Tuple, Type, Union

from tools.datetime_tools import get_utcnow_in_milliseconds, to_iso_format_datetime_string
from tools.exceptions.messages import MessageDateError, MessageIdError, MessageSourceError, MessageTypeError, \
                                      MessageValueError, MessageEpochValueError
from tools.tools import FullLogger

LOGGER = FullLogger(__name__)

# These attributes will be generated if they are not given when creating message objects.
OPTIONALLY_GENERATED_ATTRIBUTES = [
    "Timestamp"
]


def get_json(message_object: BaseMessage) -> Dict[str, Any]:
    """Returns a JSON based on the values of the given message_object and the attribute parameters."""
    return {
        json_attribute_name: (
            getattr(message_object, object_attribute_name)
            if not hasattr(getattr(message_object, object_attribute_name), 'json')
            else getattr(message_object, object_attribute_name).json()
        )
        for json_attribute_name, object_attribute_name in message_object.__class__.MESSAGE_ATTRIBUTES_FULL.items()
        if (json_attribute_name not in message_object.__class__.OPTIONAL_ATTRIBUTES_FULL or
            getattr(message_object, object_attribute_name) is not None)
    }


def validate_json(message_class: Type[BaseMessage], json_message: Dict[str, Any]) -> bool:
    """Validates the given the given json object for the attributes covered in the given message class.
        Returns True if the message is ok. Otherwise, return False."""
    for json_attribute_name, object_attribute_name in message_class.MESSAGE_ATTRIBUTES_FULL.items():
        if json_attribute_name not in json_message and json_attribute_name in OPTIONALLY_GENERATED_ATTRIBUTES:
            continue

        if (json_attribute_name not in json_message and
                json_attribute_name not in message_class.OPTIONAL_ATTRIBUTES_FULL):
            LOGGER.warning("{:s} attribute is missing from the message".format(json_attribute_name))
            return False

        if not getattr(
                message_class,
                "_".join(["_check", object_attribute_name]))(json_message.get(json_attribute_name, None)):
            # TODO: handle checking for missing timezone information
            LOGGER.warning("'{:s}' is not valid message value for {:s}".format(
                str(json_message[json_attribute_name]), json_attribute_name))
            return False

    return True


class BaseMessage():
    """The base message class for all simulation platform messages."""
    MESSAGE_ENCODING = "UTF-8"
    CLASS_MESSAGE_TYPE = ""
    MESSAGE_TYPE_CHECK = False

    # The relationships between the JSON attributes and the object properties
    MESSAGE_ATTRIBUTES = {
        "SimulationId": "simulation_id",
        "Timestamp": "timestamp"
    }
    # Attributes that can be missing from the message. Missing attributes are set to value None.
    OPTIONAL_ATTRIBUTES = []
    # attributes whose value is a QuantityBlock and the expected unit of measure.
    QUANTITY_BLOCK_ATTRIBUTES = {}

    # Full list af all attribute names, any subclass should update these with additional names.
    MESSAGE_ATTRIBUTES_FULL = MESSAGE_ATTRIBUTES
    OPTIONAL_ATTRIBUTES_FULL = OPTIONAL_ATTRIBUTES
    QUANTITY_BLOCK_ATTRIBUTES_FULL = QUANTITY_BLOCK_ATTRIBUTES

    DEFAULT_SIMULATION_ID = "simulation_id"

    def __init__(self, **kwargs):
        """Only arguments in MESSAGE_ATTRIBUTES_FULL of the message class are considered.
           If Timestamp is missing, it is added with a value corresponding to the current time.
           If one the arguments is not valid, throws an instance of MessageError.
        """
        for json_attribute_name in self.__class__.MESSAGE_ATTRIBUTES_FULL:
            setattr(self, self.__class__.MESSAGE_ATTRIBUTES_FULL[json_attribute_name],
                    kwargs.get(json_attribute_name, None))

    @property
    def simulation_id(self) -> str:
        """The simulation id."""
        return self.__simulation_id

    @property
    def timestamp(self) -> str:
        """The timestamp for the message in ISO 8601 format."""
        return self.__timestamp

    @simulation_id.setter
    def simulation_id(self, simulation_id: str):
        if self._check_simulation_id(simulation_id):
            iso_format_string = to_iso_format_datetime_string(simulation_id)
            if isinstance(iso_format_string, str):
                self.__simulation_id = iso_format_string
                return
        raise MessageDateError("'{:s}' is an invalid datetime".format(str(simulation_id)))

    @timestamp.setter
    def timestamp(self, timestamp: Union[str, datetime.datetime, None]):
        if timestamp is None:
            self.__timestamp = get_utcnow_in_milliseconds()
        else:
            if self._check_timestamp(timestamp):
                iso_format_string = to_iso_format_datetime_string(timestamp)
                if isinstance(iso_format_string, str):
                    self.__timestamp = iso_format_string
                    return

            raise MessageDateError("'{:s}' is an invalid datetime".format(str(timestamp)))

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, BaseMessage) and
            self.simulation_id == other.simulation_id and
            self.timestamp == other.timestamp
        )

    def __str__(self) -> str:
        return json.dumps(self.json())

    def __repr__(self) -> str:
        return self.__str__()

    @classmethod
    def _check_datetime(cls, datetime_value: Union[str, datetime.datetime]) -> bool:
        return to_iso_format_datetime_string(datetime_value) is not None

    @classmethod
    def _check_simulation_id(cls, simulation_id: str) -> bool:
        return cls._check_datetime(simulation_id)

    @classmethod
    def _check_timestamp(cls, timestamp: Union[str, datetime.datetime]) -> bool:
        return cls._check_datetime(timestamp)

    def json(self) -> Dict[str, Any]:
        """Returns the message as a JSON object."""
        return get_json(self)

    def bytes(self):
        """Returns the message in bytes format."""
        return bytes(json.dumps(self.json()), encoding=self.__class__.MESSAGE_ENCODING)

    @classmethod
    def validate_json(cls, json_message: Dict[str, Any]) -> bool:
        """Validates the given the given json object for the attributes covered in the given class.
           Returns True if the message is ok. Otherwise, return False."""
        return validate_json(cls, json_message)

    @classmethod
    def from_json(cls, json_message: Dict[str, Any]) -> Union[BaseMessage, None]:
        """Returns a class object created based on the given JSON attributes.
           If the given JSON does not contain valid values, returns None."""
        if cls.validate_json(json_message):
            return cls(**json_message)
        return None


class AbstractMessage(BaseMessage):
    """The abstract message class that contains the attributes that all simulation specific messages should have."""

    # The supported message types.
    # The "Type" attribute is checked against CLASS_MESSAGE_TYPE if MESSAGE_TYPE_CHECK is True.
    # For example, for EpochMessage, "Type" must be "Epoch", but for AbstractMessage any string is acceptable.
    # NOTE: this is to provide some compatibility for message types that have no implemented message class
    MESSAGE_TYPES = ["SimState", "Epoch", "Status", "Result", "General", "ResourceState"]

    # The relationships between the JSON attributes and the object properties
    MESSAGE_ATTRIBUTES = {
        "Type": "message_type",
        "SourceProcessId": "source_process_id",
        "MessageId": "message_id"
    }
    # Attributes that can be missing from the message. Missing attributes are set to value None.
    OPTIONAL_ATTRIBUTES = []

    # Full list af all attribute names, any subclass should update these with additional names.
    MESSAGE_ATTRIBUTES_FULL = {
        **BaseMessage.MESSAGE_ATTRIBUTES_FULL,
        **MESSAGE_ATTRIBUTES
    }
    OPTIONAL_ATTRIBUTES_FULL = BaseMessage.OPTIONAL_ATTRIBUTES_FULL + OPTIONAL_ATTRIBUTES

    DEFAULT_SIMULATION_ID = "simulation_id"

    @property
    def message_type(self) -> str:
        """The message type attribute."""
        return self.__message_type

    @property
    def source_process_id(self) -> str:
        """The source process id."""
        return self.__source_process_id

    @property
    def message_id(self) -> str:
        """The message id."""
        return self.__message_id

    @message_type.setter
    def message_type(self, message_type: str):
        if not self._check_message_type(message_type):
            raise MessageTypeError("'{:s}' is not an allowed message type".format(str(message_type)))
        self.__message_type = message_type

    @source_process_id.setter
    def source_process_id(self, source_process_id: str):
        if not self._check_source_process_id(source_process_id):
            raise MessageSourceError("'{:s}' is an invalid source process id".format(str(source_process_id)))
        self.__source_process_id = source_process_id

    @message_id.setter
    def message_id(self, message_id: str):
        if not self._check_message_id(message_id):
            raise MessageIdError("'{:s}' is an invalid message id".format(str(message_id)))
        self.__message_id = message_id

    def __eq__(self, other: Any) -> bool:
        return (
            super().__eq__(other) and
            isinstance(other, AbstractMessage) and
            self.message_type == other.message_type and
            self.source_process_id == other.source_process_id and
            self.message_id == other.message_id
        )

    @classmethod
    def _check_message_type(cls, message_type: str) -> bool:
        if cls.MESSAGE_TYPE_CHECK:
            return message_type == cls.CLASS_MESSAGE_TYPE
        return isinstance(message_type, str)

    @classmethod
    def _check_source_process_id(cls, source_process_id: str) -> bool:
        return isinstance(source_process_id, str) and len(source_process_id) > 0

    @classmethod
    def _check_message_id(cls, message_id: str) -> bool:
        return isinstance(message_id, str) and len(message_id) > 0

    @classmethod
    def from_json(cls, json_message: Dict[str, Any]) -> Union[AbstractMessage, None]:
        """Returns a class object created based on the given JSON attributes.
           If the given JSON does not contain valid values, returns None."""
        if cls.validate_json(json_message):
            return cls(**json_message)
        return None


class AbstractResultMessage(AbstractMessage):
    """The abstract result message class that contains the attributes that all result messages have."""
    CLASS_MESSAGE_TYPE = ""

    MESSAGE_ATTRIBUTES = {
        "EpochNumber": "epoch_number",
        "LastUpdatedInEpoch": "last_updated_in_epoch",
        "TriggeringMessageIds": "triggering_message_ids",
        "Warnings": "warnings"
    }
    OPTIONAL_ATTRIBUTES = ["LastUpdatedInEpoch", "Warnings"]

    MESSAGE_ATTRIBUTES_FULL = {
        **AbstractMessage.MESSAGE_ATTRIBUTES_FULL,
        **MESSAGE_ATTRIBUTES
    }
    OPTIONAL_ATTRIBUTES_FULL = AbstractMessage.OPTIONAL_ATTRIBUTES_FULL + OPTIONAL_ATTRIBUTES

    WARNING_TYPES = [
        "warning.convergence",
        "warning.input",
        "warning.input.range",
        "warning.input.unreliable",
        "warning.internal",
        "warning.other"
    ]

    @property
    def epoch_number(self) -> int:
        """The epoch number attribute."""
        return self.__epoch_number

    @property
    def last_updated_in_epoch(self) -> Union[int, None]:
        """The last updated in epoch attribute. It is either an epoch number or None."""
        return self.__last_updated_in_epoch

    @property
    def triggering_message_ids(self) -> List[str]:
        """The triggering message ids attribute. It is a non-empty list."""
        return self.__triggering_message_ids

    @property
    def warnings(self) -> Union[List[str], None]:
        """The warnings attribute. It is either None or a non-empty list."""
        return self.__warnings

    @epoch_number.setter
    def epoch_number(self, epoch_number: int):
        if not self._check_epoch_number(epoch_number):
            raise MessageEpochValueError("'{:s}' is not a valid epoch number".format(str(epoch_number)))
        self.__epoch_number = epoch_number

    @last_updated_in_epoch.setter
    def last_updated_in_epoch(self, last_updated_in_epoch: Union[int, None]):
        if not self._check_last_updated_in_epoch(last_updated_in_epoch):
            raise MessageEpochValueError("'{:s}' is not a valid epoch number".format(str(last_updated_in_epoch)))
        self.__last_updated_in_epoch = last_updated_in_epoch

    @triggering_message_ids.setter
    def triggering_message_ids(self, triggering_message_ids: Union[List[str], Tuple[str]]):
        if not self._check_triggering_message_ids(triggering_message_ids):
            raise MessageIdError("'{:s}' is not a valid list of message ids".format(str(triggering_message_ids)))
        self.__triggering_message_ids = list(triggering_message_ids)

    @warnings.setter
    def warnings(self, warnings: Union[List[str], Tuple[str], None]):
        if not self._check_warnings(warnings):
            raise MessageValueError("'{:s}' is not a valid list of warnings".format(str(warnings)))
        if warnings is None or (isinstance(warnings, (list, tuple)) and len(warnings) == 0):
            self.__warnings = None
        else:
            self.__warnings = list(warnings)

    def __eq__(self, other: Any) -> bool:
        return (
            super().__eq__(other) and
            isinstance(other, AbstractResultMessage) and
            self.epoch_number == other.epoch_number and
            self.last_updated_in_epoch == other.last_updated_in_epoch and
            self.triggering_message_ids == other.triggering_message_ids and
            self.warnings == other.warnings
        )

    @classmethod
    def _check_epoch_number(cls, epoch_number) -> bool:
        # epoch number 0 is reserved for the initialization phase
        return isinstance(epoch_number, int) and epoch_number >= 0

    @classmethod
    def _check_last_updated_in_epoch(cls, last_updated_in_epoch: Union[int, None]) -> bool:
        return last_updated_in_epoch is None or cls._check_epoch_number(last_updated_in_epoch)

    @classmethod
    def _check_triggering_message_ids(cls, triggering_message_ids: Union[List[str], Tuple[str]]) -> bool:
        if (triggering_message_ids is None or
                not isinstance(triggering_message_ids, (list, tuple)) or
                len(triggering_message_ids) == 0):
            return False
        for triggering_message_id in triggering_message_ids:
            if not cls._check_message_id(triggering_message_id):
                return False
        return True

    @classmethod
    def _check_warnings(cls, warnings: Union[List[str], Tuple[str], None]) -> bool:
        if warnings is None:
            return True
        if not isinstance(warnings, (list, tuple)):
            return False
        for warning in warnings:
            if warning not in cls.WARNING_TYPES:
                return False
        return True

    @classmethod
    def from_json(cls, json_message: Dict[str, Any]) -> Union[AbstractResultMessage, None]:
        """Returns a class object created based on the given JSON attributes.
           If the given JSON does not contain valid values, returns None."""
        if cls.validate_json(json_message):
            return cls(**json_message)
        return None
