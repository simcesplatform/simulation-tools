# -*- coding: utf-8 -*-

"""This module contains general utils for working with simulation platform message classes."""

from typing import Iterator, List, Optional, Type, Union

from tools.exceptions.messages import MessageError
from tools.message.abstract import AbstractMessage
from tools.message.block import QuantityBlock
from tools.message.epoch import EpochMessage
from tools.message.resource_state import ResourceStateMessage
from tools.message.simulation_state import SimulationStateMessage
from tools.message.status import StatusMessage
from tools.message.utils import get_next_message_id
from tools.tools import get_logger

LOGGER = get_logger(__name__)


def abstract_message_generator(simulation_id: str, source_process_id: str, start_message_id: int = 1) \
        -> Iterator[AbstractMessage]:
    """Generator for getting new instances of AbstractMessage with updated MessageId and Timestamp fields."""
    # TODO: add unit tests for this function
    message_id_generator = get_next_message_id(source_process_id, start_message_id)

    while True:
        try:
            new_message_id = next(message_id_generator)
        except StopIteration:
            return

        yield AbstractMessage(
            Type=AbstractMessage.CLASS_MESSAGE_TYPE,
            SimulationId=simulation_id,
            SourceProcessId=source_process_id,
            MessageId=new_message_id
        )


class MessageGenerator:
    """Message generator class to help with the creation of simulation message objects."""
    def __init__(self, simulation_id: str, source_process_id: str, start_message_id: int = 1):
        # TODO: add checks for the parameters
        self._abstract_message_generator = abstract_message_generator(
            simulation_id, source_process_id, start_message_id)

    def get_abstract_message(self) -> AbstractMessage:
        """Returns a new AbstractMessage instance."""
        return next(self._abstract_message_generator)

    def get_message(self, message_class: Type[AbstractMessage], **kwargs) -> Optional[AbstractMessage]:
        """Returns a new message instance of type message_class according to the given parameters."""
        # TODO: add unit tests for this function
        if message_class is EpochMessage:
            return self.get_epoch_message(**kwargs)
        if message_class is StatusMessage:
            return self.get_status_message(**kwargs)
        if message_class is SimulationStateMessage:
            return self.get_simulation_state_message(**kwargs)
        if message_class is ResourceStateMessage:
            return self.get_resource_state_message(**kwargs)

        if not issubclass(message_class, AbstractMessage):
            LOGGER.warning("{:s} is not a subclass of {:s}".format(
                getattr(message_class, "__name__"), AbstractMessage.__name__))
            return None

        # No predefined function for the given message class type.
        # => Argument checking is done by the message class but no error messages related to extra arguments
        #    are given as in the other cases.
        abstract_message = self.get_abstract_message()
        try:
            return message_class(
                Type=message_class.CLASS_MESSAGE_TYPE,
                SimulationId=abstract_message.simulation_id,
                SourceProcessId=abstract_message.source_process_id,
                MessageId=abstract_message.message_id,
                Timestamp=abstract_message.timestamp,
                **kwargs
            )
        except (MessageError, ValueError):
            return None

    def get_epoch_message(self, EpochNumber: int, TriggeringMessageIds: List[str],
                          StartTime: str, EndTime: str,
                          LastUpdatedInEpoch: int = None, Warnings: List[str] = None) \
            -> Optional[EpochMessage]:
        """Returns a new EpochMessage corresponding to the given parameters.
           Returns None if the message creation was unsuccessful."""
        # pylint: disable=invalid-name
        abstract_message = self.get_abstract_message()
        try:
            return EpochMessage(
                Type=EpochMessage.CLASS_MESSAGE_TYPE,
                SimulationId=abstract_message.simulation_id,
                SourceProcessId=abstract_message.source_process_id,
                MessageId=abstract_message.message_id,
                Timestamp=abstract_message.timestamp,
                EpochNumber=EpochNumber,
                TriggeringMessageIds=TriggeringMessageIds,
                LastUpdatedInEpoch=LastUpdatedInEpoch,
                Warnings=Warnings,
                StartTime=StartTime,
                EndTime=EndTime
            )
        except (MessageError, ValueError):
            return None

    def get_status_message(self, Value: str, **kwargs) -> Optional[StatusMessage]:
        """Returns a new StatusMessage corresponding to the given parameters.
           Returns None if the message creation was unsuccessful."""
        # pylint: disable=invalid-name
        if Value == StatusMessage.STATUS_VALUES[0]:   # should be "ready"
            return self.get_status_ready_message(**kwargs)
        if Value == StatusMessage.STATUS_VALUES[-1]:  # should be "error"
            return self.get_status_error_message(**kwargs)

        # unknown status value, try to create the message regardless
        abstract_message = self.get_abstract_message()
        try:
            return StatusMessage(
                Type=StatusMessage.CLASS_MESSAGE_TYPE,
                SimulationId=abstract_message.simulation_id,
                SourceProcessId=abstract_message.source_process_id,
                MessageId=abstract_message.message_id,
                Timestamp=abstract_message.timestamp,
                Value=Value,
                **kwargs
            )
        except (MessageError, ValueError):
            return None

    def get_status_ready_message(self, EpochNumber: int, TriggeringMessageIds: List[str],
                                 LastUpdatedInEpoch: int = None, Warnings: List[str] = None) \
            -> Optional[StatusMessage]:
        """Returns a new StatusMessage corresponding to the given parameters.
           Returns None if the message creation was unsuccessful."""
        # pylint: disable=invalid-name
        abstract_message = self.get_abstract_message()
        try:
            return StatusMessage(
                Type=StatusMessage.CLASS_MESSAGE_TYPE,
                SimulationId=abstract_message.simulation_id,
                SourceProcessId=abstract_message.source_process_id,
                MessageId=abstract_message.message_id,
                Timestamp=abstract_message.timestamp,
                EpochNumber=EpochNumber,
                TriggeringMessageIds=TriggeringMessageIds,
                LastUpdatedInEpoch=LastUpdatedInEpoch,
                Warnings=Warnings,
                Value=StatusMessage.STATUS_VALUES[0]  # should be "ready"
            )
        except (MessageError, ValueError):
            return None

    def get_status_error_message(self, EpochNumber: int, TriggeringMessageIds: List[str],
                                 Description: str = None,
                                 LastUpdatedInEpoch: int = None, Warnings: List[str] = None) \
            -> Optional[StatusMessage]:
        """Returns a new StatusMessage corresponding to the given parameters.
           Returns None if the message creation was unsuccessful."""
        # pylint: disable=invalid-name
        abstract_message = self.get_abstract_message()
        try:
            return StatusMessage(
                Type=StatusMessage.CLASS_MESSAGE_TYPE,
                SimulationId=abstract_message.simulation_id,
                SourceProcessId=abstract_message.source_process_id,
                MessageId=abstract_message.message_id,
                Timestamp=abstract_message.timestamp,
                EpochNumber=EpochNumber,
                TriggeringMessageIds=TriggeringMessageIds,
                LastUpdatedInEpoch=LastUpdatedInEpoch,
                Warnings=Warnings,
                Value=StatusMessage.STATUS_VALUES[0],  # should be "ready"
                Description=Description
            )
        except (MessageError, ValueError):
            return None

    def get_simulation_state_message(self, SimulationState: str, Name: str = None, Description: str = None) \
            -> Optional[SimulationStateMessage]:
        """Returns a new StatusMessage corresponding to the given parameters.
           Returns None if the message creation was unsuccessful."""
        # pylint: disable=invalid-name
        abstract_message = self.get_abstract_message()
        try:
            return SimulationStateMessage(
                Type=SimulationStateMessage.CLASS_MESSAGE_TYPE,
                SimulationId=abstract_message.simulation_id,
                SourceProcessId=abstract_message.source_process_id,
                MessageId=abstract_message.message_id,
                Timestamp=abstract_message.timestamp,
                SimulationState=SimulationState,
                Name=Name,
                Description=Description
            )
        except (MessageError, ValueError):
            return None

    def get_resource_state_message(self, EpochNumber: int, TriggeringMessageIds: List[str], Bus: str,
                                   RealPower: Union[float, QuantityBlock], ReactivePower: Union[float, QuantityBlock],
                                   LastUpdatedInEpoch: int = None, Warnings: List[str] = None,
                                   Node: int = None, StateOfCharge: Union[float, QuantityBlock] = None) \
            -> Optional[ResourceStateMessage]:
        """Returns a new StatusMessage corresponding to the given parameters.
           Returns None if the message creation was unsuccessful."""
        # pylint: disable=invalid-name
        abstract_message = self.get_abstract_message()
        try:
            return ResourceStateMessage(
                Type=EpochMessage.CLASS_MESSAGE_TYPE,
                SimulationId=abstract_message.simulation_id,
                SourceProcessId=abstract_message.source_process_id,
                MessageId=abstract_message.message_id,
                Timestamp=abstract_message.timestamp,
                EpochNumber=EpochNumber,
                TriggeringMessageIds=TriggeringMessageIds,
                LastUpdatedInEpoch=LastUpdatedInEpoch,
                Warnings=Warnings,
                Bus=Bus,
                RealPower=RealPower,
                ReactivePower=ReactivePower,
                Node=Node,
                StateOfCharge=StateOfCharge
            )
        except (MessageError, ValueError):
            return None