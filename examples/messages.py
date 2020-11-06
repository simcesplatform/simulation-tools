# -*- coding: utf-8 -*-

"""This module contains code examples related to using the message classes."""

from tools.exceptions.messages import MessageError
from tools.messages import StatusMessage, ResourceStateMessage, QuantityBlock, MessageGenerator

# define example status message in JSON format (without timestamp)
status_message_1 = {
    "Type": "Status",
    "SimulationId": "2020-11-04T07:08:56.198Z",
    "SourceProcessId": "Grid",
    "MessageId": "Grid-1",
    "EpochNumber": 0,
    "TriggeringMessageIds": [
        "simulation_manager-1"
    ],
    "Value": "ready"
}

# define example resource state message in JSON format using Quantity blocks
resource_state_1 = {
    "Type": "ResourceState",
    "SimulationId": "2020-11-04T07:08:56.198Z",
    "SourceProcessId": "load3",
    "MessageId": "load3-2",
    "EpochNumber": 1,
    "TriggeringMessageIds": [
        "simulation_manager-2"
    ],
    "Bus": "10",
    "RealPower": {
        "UnitOfMeasure": "kW",
        "Value": -0.89
    },
    "ReactivePower": {
        "UnitOfMeasure": "kV.A{r}",
        "Value": 0.0
    }
}

# define example resource state message in JSON format without using Quantity blocks
resource_state_2 = {
    "Type": "ResourceState",
    "SimulationId": "2020-11-04T07:08:56.198Z",
    "SourceProcessId": "load3",
    "MessageId": "load3-2",
    "EpochNumber": 1,
    "TriggeringMessageIds": [
        "simulation_manager-2"
    ],
    "Bus": "10",
    "RealPower": -1.89,
    "ReactivePower": 1.0
}

invalid_status_1 = {
    "Type": "Status",
    "SimulationId": "2020-11-04T07:08:56.198Z",
    "SourceProcessId": "Grid",
    "MessageId": "Grid-1",
    "EpochNumber": 0,
    "TriggeringMessageIds": [
        "simulation_manager-1"
    ]
}

invalid_status_2 = {
    "Type": "Status",
    "SimulationId": "2020-11-04T07:08:56.198Z",
    "SourceProcessId": "Grid",
    "MessageId": "Grid-1",
    "EpochNumber": 0,
    "TriggeringMessageIds": [
        "simulation_manager-1"
    ],
    "Value": "hello"
}


def test_from_json():
    """Tests for creating message objects using from_json method."""
    print()
    status1 = StatusMessage.from_json(status_message_1)
    print("Status1:", type(status1), status1)
    print()
    resource1 = ResourceStateMessage.from_json(resource_state_1)
    print("ResourceState1:", type(resource1), resource1)
    print()
    resource2 = ResourceStateMessage.from_json(resource_state_2)
    print("ResourceState2:", type(resource2), resource2)
    print()
    print(status1.message_id)
    print(status1.epoch_number)
    print(status1.timestamp)
    print()
    print(resource1.message_id)
    print(type(resource1.real_power), resource1.real_power)
    print(resource1.real_power.value, resource1.real_power.unit_of_measure)
    print()
    print(type(resource2.real_power), resource2.real_power)
    print(resource2.real_power.value, resource2.real_power.unit_of_measure)


def test_invalid_status():
    """Tests for trying to create status message instances with invalid values."""
    print()
    invalid1 = StatusMessage.from_json(invalid_status_1)
    print(type(invalid1), invalid1)
    print()
    invalid2 = StatusMessage.from_json(invalid_status_2)
    print(type(invalid2), invalid2)
    print()

    # Note:     StatusMessage(**{"attr1": value1, "attr2": value2})
    # is the as StatusMessage(attr1=value1, attr2=value)
    try:
        invalid1 = StatusMessage(**invalid_status_1)
    except MessageError as error:
        print("Exception thrown:", error)

    try:
        invalid2 = StatusMessage(Type="Status")
    except MessageError as error:
        print("Exception thrown:", error)


def test_message_generator():
    """Examples for using the message generator."""
    print()
    message_generator = MessageGenerator(
        simulation_id="2020-11-01T00:00:00.000Z",
        source_process_id="Storage")

    status1 = message_generator.get_message(
        StatusMessage,
        EpochNumber=0,
        TriggeringMessageIds=["manager-1"],
        Value="ready")
    print(type(status1), status1)
    print()
    status2 = message_generator.get_status_ready_message(
        EpochNumber=1,
        TriggeringMessageIds=["manager-2"])
    print(type(status2), status2)
    print()
    resource1 = message_generator.get_message(
        ResourceStateMessage,
        EpochNumber=1,
        TriggeringMessageIds=["some-message"],
        Bus="somebus",
        RealPower=12.3,
        ReactivePower=0.5)
    print(type(resource1), resource1)
    print()
    resource2 = message_generator.get_resource_state_message(
        EpochNumber=1,
        TriggeringMessageIds=["some-message"],
        Bus="somebus",
        RealPower=12.3,
        ReactivePower=0.5)
    print(type(resource2), resource2)
    print()
    try:
        resource3 = message_generator.get_message(
            ResourceStateMessage,
            EpochNumber=1,
            TriggeringMessageIds=["some-message"],
            RealPower=12.3
        )
        print(type(resource3), resource3)
    except TypeError as error:
        print("exception:", error)
    print()


# define example resource state message in JSON format using Quantity blocks
resource_state_3 = {
    "Type": "ResourceState",
    "SimulationId": "2020-11-04T07:08:56.198Z",
    "SourceProcessId": "load3",
    "MessageId": "load3-2",
    "EpochNumber": 1,
    "TriggeringMessageIds": [
        "simulation_manager-2"
    ],
    "Bus": "10",
    "RealPower": QuantityBlock(Value=-0.89, UnitOfMeasure="kW"),
    "ReactivePower": QuantityBlock(Value=0.0, UnitOfMeasure="kV.A{r}")
}
