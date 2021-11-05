# /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This module contains implementations of built-in endpoints.
"""

class ConnectionResource:
    """A custom resource object that is built to be used with `RestApiHandler`.

    This class is to be extended and used like the `Resource` class.
    Have `get()`, `post()`, and other methods for the types of responses you need.
    """

    # functions will be implemented in subclasses

import typing as t


def send(conn) -> t.Type[ConnectionResource]:
    """
    """


def receive(conn) -> t.Type[ConnectionResource]:
    """
    """


def get(conn) -> t.Type[ConnectionResource]:
    """
    """


def get_first_response(conn) -> t.Type[ConnectionResource]:
    """
    """


def wait_for_response(conn) -> t.Type[ConnectionResource]:
    """
    """


def send_for_response(conn) -> t.Type[ConnectionResource]:
    """
    """


def list_ports(conn) -> t.Type[ConnectionResource]:
    """
    """


def all_endpoints() -> None:
    """
    Returns a list of all functions and their endpoints as tuples (endpoint, function)
    """

    return [
        ("/send", send),
        ("/receive", receive),
        ("/get", get),
        ("/send/get_first", get_first_response),
        ("/get/wait", wait_for_response),
        ("/send/get", send_for_response),
        ("/list_ports", list_ports)
    ]
