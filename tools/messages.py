# -*- coding: utf-8 -*-

"""This module contains a class for creating and holding messages for the RabbitMQ message bus."""

# import these for backwards compatibility
from tools.message.abstract import BaseMessage, AbstractMessage     # pylint: disable=unused-import
from tools.message.abstract import AbstractResultMessage, get_json  # pylint: disable=unused-import
from tools.message.utils import get_next_message_id                 # pylint: disable=unused-import
from tools.message.generator import MessageGenerator                # pylint: disable=unused-import

from tools.message.simulation_state import SimulationStateMessage
from tools.message.epoch import EpochMessage
from tools.message.status import StatusMessage
from tools.message.resource_state import ResourceStateMessage
from tools.message.general import GeneralMessage, ResultMessage
from tools.tools import FullLogger

LOGGER = FullLogger(__name__)


MESSAGE_TYPES = {
    "SimState": SimulationStateMessage,
    "Epoch": EpochMessage,
    "Status": StatusMessage,
    "ResourceState": ResourceStateMessage,
    "Result": ResultMessage,
    "General": GeneralMessage
}
DEFAULT_MESSAGE_TYPE = "General"
