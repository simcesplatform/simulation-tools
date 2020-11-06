# -*- coding: utf-8 -*-

"""This module contains code example to instantiate RabbitmqClient object."""

from tools.clients import RabbitmqClient


def get_client():
    """Returns a RabbitmqClient instance."""
    # Replace the parameters with proper values for host, port, login and password
    # Change the value of exchange if needed.
    return RabbitmqClient(
        host="",
        port=0,
        login="",
        password="",
        exchange="procem.examples_testing",
        ssl=True,
        ssl_version="PROTOCOL_TLS",
        exchange_autodelete=True,
        exchange_durable=False
    )
