# Simulation Tools

Tools for working with simulation messages and with the RabbitMQ message bus in Python.

## Contents

- [`tools/callbacks.py`](tools/callbacks.py)
    - Contains MessageCallback class that can convert a message received from the message bus to a Message object.
    - Used also by tools.clients.RabbitmqClient when setting up topic listeners.
- [`tools/clients.py`](tools/clients.py)
    - Contains RabbitmqClient that can be used as a client to send and receive messages to and from RabbitMQ message bus.
    - Uses the asynchronous RabbitMQ library aio_pika.
    - One client can handle messaging only for one exchange. Separate clients are needed if more than one exchanges are used.
    - Methods for RabbitmqClient:
        - `__init__` (constructor):
            - Used for creating a new client instance with the given parameters.
            - `host`
                - the host name for the RabbitMQ server
            - `port`
                - the port number for the RabbitMQ server
            - `login`
                - username for access to the RabbitMQ server
            - `password`
                - password for access to the RabbitMQ server
            - `ssl`
                - use SSL connection to the RabbitMQ server
            - `ssl_version`
                - the SSL version parameter for the SSL connection
            - `exchange`
                - the name for the exchange used by the client
            - `exchange_autodelete`
                - whether to automatically delete the exchange after use
            - `exchange_durable`
                - whether to setup the exchange to survive message bus restarts
        - `add_listener`
            - Used for adding a message listener for the given topic(s).
            - `topic_names`
                - Either a single topic name or a list of topic names
            - `callback_function`
                - The function which will called when new message is received.
                - The function must be awaitable and it must callable with two parameters: the message object and the topic name.
        - `send_message`
            - Used for sending a new message to a given topic.
            - `topic_name`
                - The topic to be used when sending the message
            - `message_bytes`
                - The message in bytes format
        - `close`
            - Used for closing the message bus connection.
            - Should always called before exiting the program.

- [`tools/components.py`](tools/components.py)
    - Contains AbstractSimulationComponent that can be used as base class when creating new simulation component.
    - Uses tools.clients.RabbitmqClient for the message bus communication.
    - Contains the base workflow common for any simulation component.
        - Sends Status ready message after receiving SimState running message.
        - Stops the component after receiving SimState stopped message.
        - Provides functions that user can overwrite to create new components for a specific use cases.
        - Sends Status ready message automatically after the component is finished with the current epoch.
        - Methods for AbstractSimulationComponent:
            - `__init__` (constructor)
                - `simulation_id`
                    - The simulation id for the simulation run
                - `component_name`
                    - The component name, i.e. the source process id, for the simulation run
                - The RabbitMQ connection parameters are taken from environmental variables. In a future update, the parameters could be alternatively given as constructor parameters.
                - Also the simulation_id and component_name can be given as environmental variables.
            - `start`
                - Starts the component including setting up the message bus topic listeners.
                - TODO: provide the user a way to give additional topics that are listened to
            - `stop`
                - Stops the component including closing the message bus connection.
            - `general_message_handler`
                - Should be overwritten when creating new component.
                - Should handle all received messages except SimState and Epoch messages.
                - `message_object`
                    - The received message object or a dictionary containing the message in cases where there was no message class available for the message type.
                - `message_routing_key`
                    - The topic name for the received message
            - `all_messages_received_for_epoch`
                - Should be overwritten when creating new component.
                - Should check that all the messages required to start calculations for the current epoch have been received.
                - Checking for a new Epoch message as well as for the simulation state is done automatically by AbstractSimulationComponent.
                - Should return True, if the component is ready to handle the current epoch. Otherwise, should return False.
            - `process_epoch`
                - Should be overwritten when creating new component.
                - Should do the calculations for the current epoch.
                - Should send all the result messages to the message bus.
                - Should return True, if the component is finished with current epoch. Otherwise, should return False.
            - `start_epoch`
                - Checks if the component is ready to do the calculations for the current epoch, using `ready_for_new_epoch`, and if that is the case calls `process_epoch`. If the `process_epoch` returns true, sends a Status ready message to the message bus.
                - Should be called whenever it is possible that the component is ready to proceed with the current epoch, I.e. usually after handling a received message in `general_message_handler`.
                - The function is called automatically after each Epoch message.

- [`tools/datetime_tools.py`](tools/datetime_tools.py)
    - Contains tools for handling datetime objects and strings.
    - `get_utcnow_in_milliseconds`
        - Returns the current ISO 8601 format datetime string in UTC timezone.
    - `to_iso_format_datetime_string`
        - `datetime_value`
            - A datetime value given either as a string or as a datetime object.
        - Returns the given datetime_value as a ISO 8601 formatted string in UTC timezone.
        - Returns None if the given string is not in an appropriate format.
    - `to_utc_datetime_object`
        - `datetime_str`
            - A datetime given as a ISO 8601 formatted string
        - Returns the corresponding datetime object.

- [`tools/db_clients.py`](tools/db_clients.py)
    - Contains a MongodbClient client that can be used to store messages to Mongo database.
    - Currently contains mainly functionalities required by Log Writer.

- [`tools/messages.py`](tools/messages.py)
    - Contains message classes that can be used to handle messages in the simulation platform.
    - The timestamps for the message objects are generated automatically if the timestamp is not explicitly given.
    - The actual source for the message classes can be found in the folder `tools/message/` but the this file can be used to simplify import calls.
    - Currently supported message types:
        - `BaseMessage`
            - Message object that contains only SimulationId and Timestamp
            - Log Writer can handle any message that contains at least there two attributes.
        - `AbstractMessage`
            - Child class of BaseMessage
            - Adds Type, SourceProcessId and MessageId attributes
            - Definition: [AbstractMessage](https://wiki.eduuni.fi/pages/viewpage.action?spaceKey=tuniSimCES&title=AbstractMessage)
        - `AbstractResultMessage`
            - Child class of AbstractMessage
            - Adds EpochNumber, LastUpdatedInEpoch, TriggeringMessageIds and Warnings
            - Definition [AbstractResult](https://wiki.eduuni.fi/display/tuniSimCES/AbstractResult)
        - `SimulationStateMessage`
            - Child class of AbstractMessage
            - Adds SimulationState, Name and Description
            - Definition: [SimState](https://wiki.eduuni.fi/display/tuniSimCES/SimState)
        - `EpochMessage`
            - Child class of AbstractResultMessage
            - Adds StartTime and EndTime
            - Definition: [Epoch](https://wiki.eduuni.fi/display/tuniSimCES/Epoch)
        - `StatusMessage`
            - Child class of AbstractResultMessage
            - Adds Value and Description
            - Definition: [Status](https://wiki.eduuni.fi/display/tuniSimCES/Status)
        - `ResourceStateMessage`
            - Child class of AbstractResultMessage
            - Adds Bus, RealPower, ReactivePower, Node and StateOfCharge
            - Definition: [ResourceState](https://wiki.eduuni.fi/display/tuniSimCES/ResourceState)
        - `ResultMessage`
            - Child class of AbstractResultMessage
            - Can add any user chosen attributes but does not provide any checks for validity of the attribute values.
            - Can be useful for testing but should not be used in production ready components.
        - `GeneralMessage`
            - Child class of BaseMessage
            - Similar to ResultMessage but only requires the SimulationId and Timestamp attributes
    - Common methods for all message classes:
        - `__init__` (constructor)
            - Takes in all the arguments as defined in the wiki pages for the message.
            - Any additional argument that is not part of the message definition is ignored.
            - Does some validity checks for the attribute values and throws an exception if at least one value was found to be invalid. For example, the EpochNumber must be a non-negative integer.
        - `from_json` (class method)
            - Returns a new message instance if the `json_message` contains valid values for the message type. Returns None, if there is at least one invalid value.
            - Can be used instead of the constructor to avoid exception handling.
        - `json`
            - Returns the message instance as a Python dictionary.
        - `bytes`
            - Returns the message instance in UTF-8 encoded bytes format.
        - property getters and setters for each message attribute
    - Class for QuantityBlock that can be used as a message attribute
        - QuantityBlock is constructed similarly to the message classes
        - Supports Value and UnitOfMeasure attributes
        - Definition: [Quantity block](https://wiki.eduuni.fi/display/tuniSimCES/Quantity+block)
    - MessageGenerator class for creating a series message of messages that have common SimulationId and SourceProcessId.
        - `__init__` (constructor)
            - `simulation_id`
                - The simulation id for the messages.
            - `source_process_id`
                - The source process id, i.e. the component name for the messages.
        - `get_message`
            - Returns a new message instance or None if some attributes were invalid.
                - `message_class`
                    - The message class name for the new message instance.
                - `**kwargs`
                    - All the appropriate attributes for the message. Type, SimulationId, SourceProcessId, MessageId and Timestamp are not required.
        - Special methods for generating specific message types.
    - Note: the current implementation of the message classes is quite verbose. The implementation might be changed in order to make it easier to create additional message classes. However, the interface, i.e. how the messages are created or used, will not change.

- [`tools/timer.py`](tools/timer.py)
    - Contains Timer class that can be used to setup timed tasks.
    -
- [`tools/timeseries.py`](tools/timeseries.py)
    - Contains classes for generating time series blocks for simulation messages.
    - Will be moved under message folder in future updates.

- [`tools/tools.py`](tools/tools.py)
    - Contains tools that can be used to fetch environmental variables and to setup a logger object.

## Run unit tests

```bash
docker network create tools_test_network
docker-compose -f rabbitmq/docker-compose-rabbitmq.yml up --detach
docker-compose -f mongodb/docker-compose-mongodb.yml up --detach
# Wait a few seconds to allow the local RabbitMQ message bus to initialize.
docker-compose -f docker-compose-tests.yml up --build
```

## Clean up after running the tests

```bash
docker-compose -f rabbitmq/docker-compose-rabbitmq.yml down --remove-orphans
docker-compose -f mongodb/docker-compose-mongodb.yml down --remove-orphans
docker-compose -f docker-compose-tests.yml down --remove-orphans
docker network rm tools_test_network
```
