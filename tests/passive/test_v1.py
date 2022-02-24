#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from com_server import Connection, ConnectionRoutes, RestApiHandler
from com_server.api import V1
import pytest


def test_all_routes_being_added() -> None:
    """Tests that all routes from V1 API are being added with correct prefix"""

    conn = Connection(115200, "/dev/ttyUSB0")
    handler = ConnectionRoutes(conn)

    pref = "testpref"

    # should not raise anything
    V1(handler, pref)

    _endpoints = [
        "/send",
        "/receive/<int:num_before>",
        "/receive",
        "/get",
        "/first_response",
        "/send_until",
        "/connection_state",
        "/all_ports",
    ]

    for i in _endpoints:
        assert f"/{pref}{i}" in handler.all_resources


def test_not_connection_routes_raises_exception() -> None:
    """Tests that wrapping other class should raise an exception"""

    conn = Connection(115200, "/dev/ttyUSB0")
    handler = RestApiHandler(conn)

    with pytest.raises(TypeError):
        V1(handler)
