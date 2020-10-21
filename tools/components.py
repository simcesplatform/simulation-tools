# -*- coding: utf-8 -*-

"""This module contains a base simulation component that can communicate with the RabbitMQ message bus."""

from typing import cast, Any, Union

from tools.clients import RabbitmqClient
from tools.messages import BaseMessage, EpochMessage, StatusMessage, SimulationStateMessage, \
                           get_next_message_id
from tools.tools import FullLogger, load_environmental_variables

LOGGER = FullLogger(__name__)

# The names of the environmental variables used by the component.
SIMULATION_ID = "SIMULATION_ID"
SIMULATION_COMPONENT_NAME = "SIMULATION_COMPONENT_NAME"
SIMULATION_EPOCH_MESSAGE_TOPIC = "SIMULATION_EPOCH_MESSAGE_TOPIC"
SIMULATION_STATUS_MESSAGE_TOPIC = "SIMULATION_STATUS_MESSAGE_TOPIC"
SIMULATION_STATE_MESSAGE_TOPIC = "SIMULATION_STATE_MESSAGE_TOPIC"
SIMULATION_ERROR_MESSAGE_TOPIC = "SIMULATION_ERROR_MESSAGE_TOPIC"


class AbstractSimulationComponent:
    """Class for holding the state of a abstract simulation component.
       The actual simulation components should be derived from this."""
    SIMULATION_STATE_VALUE_RUNNING = SimulationStateMessage.SIMULATION_STATES[0]   # "running"
    SIMULATION_STATE_VALUE_STOPPED = SimulationStateMessage.SIMULATION_STATES[-1]  # "stopped"

    READY_STATUS = StatusMessage.STATUS_VALUES[0]  # "ready"
    ERROR_STATUS = StatusMessage.STATUS_VALUES[-1]  # "error"

    def __init__(self):
        """Loads the simulation is and the component name as wells as the required topic names from environmental
           variables and sets up the connection to the RabbitMQ message bus for which the connection parameters are
           fetched from environmental variables. Opens a topic listener for the simulation state and epoch messages
           after creating the connection to the message bus.
        """
        # Load the component specific environmental variables.
        env_variables = load_environmental_variables(
            (SIMULATION_ID, str),
            (SIMULATION_COMPONENT_NAME, str, "component"),
            (SIMULATION_EPOCH_MESSAGE_TOPIC, str, "Epoch"),
            (SIMULATION_STATUS_MESSAGE_TOPIC, str, "Status.Ready"),
            (SIMULATION_STATE_MESSAGE_TOPIC, str, "SimState"),
            (SIMULATION_ERROR_MESSAGE_TOPIC, str, "Status.Error")

        )

        # Start the connection to the RabbitMQ client with the parameter values read from environmental variables.
        self._rabbitmq_client = RabbitmqClient()

        self._simulation_id = cast(str, env_variables[SIMULATION_ID])
        self._component_name = cast(str, env_variables[SIMULATION_COMPONENT_NAME])
        self._is_stopped = True
        self.initialization_error = None

        self._simulation_state_topic = cast(str, env_variables[SIMULATION_STATE_MESSAGE_TOPIC])
        self._epoch_topic = cast(str, env_variables[SIMULATION_EPOCH_MESSAGE_TOPIC])
        self._status_topic = cast(str, env_variables[SIMULATION_STATUS_MESSAGE_TOPIC])
        self._error_topic = cast(str, env_variables[SIMULATION_ERROR_MESSAGE_TOPIC])

        self._simulation_state = AbstractSimulationComponent.SIMULATION_STATE_VALUE_STOPPED
        self._latest_epoch = 0
        self._completed_epoch = 0
        self._triggering_message_ids = [""]
        self._latest_status_message_id = None
        self._latest_epoch_message = None

        self._message_id_generator = get_next_message_id(self._component_name)

    @property
    def simulation_id(self) -> str:
        """The simulation ID for the simulation."""
        return self._simulation_id

    @property
    def component_name(self) -> str:
        """The component name in the simulation."""
        return self._component_name

    @property
    def is_stopped(self) -> bool:
        """Returns True, if the component is stopped."""
        return self._is_stopped

    @property
    def is_client_closed(self) -> bool:
        """Returns True if the RabbitMQ client has been stopped."""
        return self._rabbitmq_client is None or self._rabbitmq_client.is_closed

    @property
    def initialization_error(self) -> Union[str, None]:
        """If the component has encountered an error during initialization contains an errorr message.
        If there was no error will be None."""
        return self._initialization_error

    @initialization_error.setter
    def initialization_error(self, initialization_error: Union[str, None]):
        """Set the initialization error message."""
        self._initialization_error = initialization_error

    async def start(self) -> None:
        """Starts the component."""
        if self.is_client_closed:
            self._rabbitmq_client = RabbitmqClient()

        LOGGER.info("Starting the component: '{:s}'".format(self.component_name))
        self._rabbitmq_client.add_listener(
            [
                self._simulation_state_topic,
                self._epoch_topic
            ],
            self.general_message_handler)
        self._is_stopped = False

    async def stop(self) -> None:
        """Stops the component."""
        LOGGER.info("Stopping the component: '{:s}'".format(self.component_name))
        self._simulation_state = AbstractSimulationComponent.SIMULATION_STATE_VALUE_STOPPED
        await self._rabbitmq_client.close()
        self._is_stopped = True

    def get_simulation_state(self) -> str:
        """Returns the simulation state attribute."""
        return self._simulation_state

    async def set_simulation_state(self, new_simulation_state: str) -> None:
        """Sets the simulation state. If the new simulation state is "running" and the current epoch is 0,
           sends a status message to the message bus. If initialization_error is None sends a ready status message.
           If it contains an error message sends an error status.
           If the new simulation state is "stopped", stops the dummy component."""
        if new_simulation_state in SimulationStateMessage.SIMULATION_STATES:
            self._simulation_state = new_simulation_state

            if new_simulation_state == AbstractSimulationComponent.SIMULATION_STATE_VALUE_RUNNING:
                if self._latest_epoch == 0:
                    if self.initialization_error is None:
                        await self.send_status_message()

                    else:
                        # the component could not be initialized properly
                        await self.send_error_message(self.initialization_error)

            elif new_simulation_state == AbstractSimulationComponent.SIMULATION_STATE_VALUE_STOPPED:
                await self.stop()

    async def start_epoch(self) -> bool:
        """Starts a new epoch for the component.
           Returns True if the epoch calculations were completed for the current epoch.
        """
        if self._simulation_state == AbstractSimulationComponent.SIMULATION_STATE_VALUE_STOPPED:
            LOGGER.warning("Simulation is stopped, cannot start epoch calculations")
            return False

        if self._latest_epoch_message is None:
            LOGGER.warning("No epoch message received, cannot start epoch calculations.")
            return False

        if self._simulation_state != AbstractSimulationComponent.SIMULATION_STATE_VALUE_RUNNING:
            LOGGER.warning("Simulation in an unknown state: '{:s}', cannot start epoch calculations.".format(
                self._simulation_state))
            return False

        self._latest_epoch = self._latest_epoch_message.epoch_number

        # Any calculations done within the epoch would be included here.
        # Also, any possible checks for additional information that is required would be done here.
        return True

    async def general_message_handler(self, message_object: Union[BaseMessage, Any],
                                      message_routing_key: str) -> None:
        """Forwards the message handling to the appropriate function depending on the message type."""
        if isinstance(message_object, SimulationStateMessage):
            await self.simulation_state_message_handler(message_object, message_routing_key)

        elif isinstance(message_object, EpochMessage):
            await self.epoch_message_handler(message_object, message_routing_key)

        else:
            # Handling of any other message types would be added here.
            pass

    async def simulation_state_message_handler(self, message_object: SimulationStateMessage,
                                               message_routing_key: str) -> None:
        """Handles the received simulation state messages."""
        if message_object.simulation_id != self.simulation_id:
            LOGGER.info(
                "Received state message for a different simulation: '{:s}' instead of '{:s}'".format(
                    message_object.simulation_id, self.simulation_id))
        elif message_object.message_type != SimulationStateMessage.CLASS_MESSAGE_TYPE:
            LOGGER.info(
                "Received a state message with wrong message type: '{:s}' instead of '{:s}'".format(
                    message_object.message_type, SimulationStateMessage.CLASS_MESSAGE_TYPE))
        else:
            LOGGER.debug("Received a state message from {:s} on topic {:s}".format(
                message_object.source_process_id, message_routing_key))
            self._triggering_message_ids = [message_object.message_id]
            await self.set_simulation_state(message_object.simulation_state)

    async def epoch_message_handler(self, message_object: EpochMessage, message_routing_key: str) -> None:
        """Handles the received epoch messages."""
        if message_object.simulation_id != self.simulation_id:
            LOGGER.info(
                "Received epoch message for a different simulation: '{:s}' instead of '{:s}'".format(
                    message_object.simulation_id, self.simulation_id))
        elif message_object.message_type != EpochMessage.CLASS_MESSAGE_TYPE:
            LOGGER.info(
                "Received a epoch message with wrong message type: '{:s}' instead of '{:s}'".format(
                    message_object.message_type, EpochMessage.CLASS_MESSAGE_TYPE))
        elif (message_object.epoch_number == self._latest_epoch and
              self._latest_status_message_id in message_object.triggering_message_ids):
            LOGGER.info("Status message has already been registered for epoch {:d}".format(self._latest_epoch))
        else:
            LOGGER.debug("Received an epoch from {:s} on topic {:s}".format(
                message_object.source_process_id, message_routing_key))
            self._triggering_message_ids = [message_object.message_id]
            self._latest_epoch_message = message_object

            # If all the epoch calculations were completed, send a new status message.
            if await self.start_epoch():
                self._completed_epoch = self._latest_epoch
                await self.send_status_message()

    async def send_status_message(self) -> None:
        """Sends a new status message to the message bus."""
        status_message = self._get_status_message()
        if status_message is None:
            await self.send_error_message("Internal error when creating status message.")
        else:
            await self._rabbitmq_client.send_message(self._status_topic, status_message.bytes())
            self._completed_epoch = self._latest_epoch

    async def send_error_message(self, description: str) -> None:
        """Sends an error message to the message bus."""
        error_message = self._get_error_message(description)
        if error_message is None:
            # So serious error that even the error message could not be created => stop the component.
            await self.stop()
        else:
            await self._rabbitmq_client.send_message(self._error_topic, error_message.bytes())

    def _get_status_message(self) -> Union[StatusMessage, None]:
        """Creates a new status message and returns the created message object.
           Returns None, if there was a problem creating the message."""
        status_message = StatusMessage.from_json({
            "Type": StatusMessage.CLASS_MESSAGE_TYPE,
            "SimulationId": self.simulation_id,
            "SourceProcessId": self.component_name,
            "MessageId": next(self._message_id_generator),
            "EpochNumber": self._latest_epoch,
            "TriggeringMessageIds": self._triggering_message_ids,
            "Value": self.__class__.READY_STATUS
        })
        if status_message is None:
            LOGGER.error("Problem with creating a status message")
            return None

        self._latest_status_message_id = status_message.message_id
        return status_message

    def _get_error_message(self, description: str) -> Union[StatusMessage, None]:
        """Creates a new error message and returns the created message object.
           Returns None, if there was a problem creating the message."""
        error_message = StatusMessage.from_json({
            "Type": StatusMessage.CLASS_MESSAGE_TYPE,
            "SimulationId": self.simulation_id,
            "SourceProcessId": self.component_name,
            "MessageId": next(self._message_id_generator),
            "EpochNumber": self._latest_epoch,
            "TriggeringMessageIds": self._triggering_message_ids,
            "Value": self.__class__.ERROR_STATUS,
            "Description": description
        })
        if error_message is None:
            LOGGER.error("Problem with creating an error message")
            return None

        return error_message
