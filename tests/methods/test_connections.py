#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests the connection endpoints such as connected() and list_ports()
"""

import json

from com_server import all_ports
import pytest
import requests

SERVER = "http://127.0.0.1:8080"

# don't start unless running
try:
    requests.get(SERVER+"/recall")
except requests.exceptions.ConnectionError:
    pytestmark = pytest.mark.skip(
        reason="Server not launched. Make sure it is running on 0.0.0.0 with port 8080, or run \"com_server run <baud> <serport>\".")


def test_register() -> None:
    r = requests.get(SERVER + "/register")
    assert r.status_code == 200


def test_connected():
    """
    Arduino should be connected
    """

    r = requests.get(SERVER+"/connected")
    loaded = json.loads(r.text)

    assert r.status_code == 200 and loaded["connected"] == True


def test_list_ports():
    """
    Tests that com_server.list_ports() is the same as the data from request
    """

    r = requests.get(SERVER+"/list_ports")
    loaded = json.loads(r.text)

    a = all_ports()
    for i in range(len(a)):
        for j in range(len(loaded["ports"][i])):
            assert loaded["ports"][i][j] == a[i][j]

    assert r.status_code == 200


def test_unregister() -> None:
    r = requests.get(SERVER + "/recall")
    assert r.status_code == 200
