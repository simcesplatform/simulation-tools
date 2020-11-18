# -*- coding: utf-8 -*-

"""This module contains some message examples in JSON format."""

# NOTE: Here all examples are given as Python dictionaries that are a superset for JSON objects.
#       I.e. all JSON objects cab be Python dictionaries but not all Python dictionaries are JSON objects.

# define example status ready message in JSON format (without timestamp or optional attributes)
status_ready_message = {
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

# define example status error message in JSON format
status_error_message = {
    "Type": "Status",
    "SimulationId": "2020-11-04T07:15:00.222Z",
    "SourceProcessId": "Grid",
    "MessageId": "Grid-6",
    "EpochNumber": 5,
    "TriggeringMessageIds": [
        "simulation_manager-1"
    ],
    "LastUpdatedInEpoch": 5,
    "Warnings": ["warning.internal"],
    "Value": "error",
    "Description": "Description for the error"
}

# example of an invalid Status message that is missing the "Value" attribute
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

# example of an invalid Status message that has an invalid value for the attribute "Value"
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

# example of an invalid Status message that has an invalid value for the attribute "EpochNumber"
invalid_status_3 = {
    "Type": "Status",
    "SimulationId": "2020-11-04T07:08:56.198Z",
    "SourceProcessId": "Grid",
    "MessageId": "Grid-1",
    "EpochNumber": -5,
    "TriggeringMessageIds": [
        "simulation_manager-1"
    ],
    "Value": "ready"
}
