# Simulation Tools

Tools for working with simulation messages and with the RabbitMQ message bus in Python.

## Contents

- [`tools/callbacks.py`](tools/callbacks.py)
    - Contains tools for converting the message received from the message bus to a Message object.
- [`tools/clients.py`](tools/clients.py)
    - Contains a client that can be used to send and receive messages to and from RabbitMQ message bus.
- [`tools/datetime_tools.py`](tools/datetime_tools.py)
    - Contains tools for handling with datetime objects.
- [`tools/messages.py`](tools/messages.py)
    - Contains message classes that can be used to handle messages in the simulation platform.
- [`tools/timer.py`](tools/timer.py)
    - Contains timer class that can be used to setup timed tasks.
- [`tools/tools.py`](tools/tools.py)
    - Contains tools that can be used to fetch environmental variables and to setup a logger object.

## Run unit tests

```bash
docker network create tools_test_network
docker-compose -f rabbitmq/docker-compose-rabbitmq.yml up --detach
docker-compose -f docker-compose-tests.yml up --build
```
