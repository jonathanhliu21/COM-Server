#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests binary search of BaseConnection
"""

from com_server import BaseConnection

def test_bin_srch() -> None:
    b = BaseConnection(port="test", baud=123)

    b._rcv_queue = [
        (1636911273.8617003, b""),
        (1636911274.8653774, b""),
    ]
    assert b._binary_search_rcv(1636911273.8617003) == 0
