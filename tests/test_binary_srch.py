#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests binary search of BaseConnection and exception thrown when available is called while disconnected
"""

import pytest
from com_server import Connection, ConnectException

def test_bin_srch() -> None:
    b = Connection(port="test", baud=123)

    b._rcv_queue = [
        (1636911273.8617003, b""),
        (1636911274.8653774, b""),
    ]
    assert b._binary_search_rcv(1636911273.8617003) == 0


def test_available_exception() -> None:
    """
    Tests that calling available while not connected will raise exception
    """

    b = Connection(port="test", baud=123)
    with pytest.raises(ConnectException):
        b.available
