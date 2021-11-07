#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
For testing things with server running. 
Make sure server is running on local computer with host "0.0.0.0" and port "8080" before testing.
"""

import json
import os
import sys

import pytest
import requests
from com_server import (BaseConnection, Connection, ConnectionResource,
                        RestApiHandler, Builtins)

SERVER = "http://0.0.0.0:8080"

# don't start unless running
try:
    requests.get(SERVER+"/recall")
except requests.exceptions.ConnectionError:
    pytestmark = pytest.mark.skip(
        reason="Server not launched. Make sure it is running on 0.0.0.0 with port 8080, or run \"python3 tests/start_server.py\".")


def test_register() -> None:
    r = requests.get(SERVER + "/register")
    assert r.status_code == 200


def test_register_after_registered() -> None:
    r = requests.get(SERVER + "/register")
    assert r.status_code == 400


def test_send() -> None:
    data = {
        "data": [1, 2, 3, 4],
        "ending": "\n",
        "concatenate": ";"
    }

    # normal test (tests send with data)
    r = requests.post(SERVER + "/send", data=data)
    print("send:", r.text)
    loaded = json.loads(r.text)
    assert "message" in loaded and loaded["message"] == "OK"
    assert r.status_code == 200

    # tests parses correctly
    data["notanarg"] = "notanarg"
    r = requests.post(SERVER + "/send", data=data)
    print("send:", r.text)
    loaded = json.loads(r.text)
    assert "message" in loaded
    assert r.status_code == 400

    # tests that send interval is working
    del data["notanarg"]
    r = requests.post(SERVER + "/send", data=data)
    print("send:", r.text)
    loaded = json.loads(r.text)
    assert "message" in loaded and loaded["message"] == "Failed to send"
    assert r.status_code == 502


def test_receive() -> None:
    data = {
        "num_before": 0,
        "read_until": None,
        "strip": True
    }

    # tests post is working
    r = requests.post(SERVER + "/receive", data=data)
    print("rcv:", r.text)
    loaded = json.loads(r.text)
    assert "message" in loaded and loaded["message"] == "OK" and "timestamp" in loaded and "data" in loaded
    assert r.status_code == 200

    # tests get is working
    r = requests.get(SERVER + "/receive", data=data)
    print("rcv:", r.text)
    loaded = json.loads(r.text)
    assert "message" in loaded and loaded["message"] == "OK" and "timestamp" in loaded and "data" in loaded
    assert r.status_code == 200

def test_rcv_all() -> None:
    # tests get
    r = requests.get(SERVER + "/receive/all")
    print("rcv all:", r.text)
    loaded = json.loads(r.text)
    assert "message" in loaded and loaded["message"] == "OK" and isinstance(loaded["timestamps"], list) and isinstance(loaded["data"], list)
    assert r.status_code == 200

    # tests post
    data = {
        "read_until": ";",
        "strip": True
    }

    r = requests.post(SERVER + "/receive/all", data=data)
    print("rcv all:", r.text)
    loaded = json.loads(r.text)
    assert "message" in loaded and loaded["message"] == "OK" and isinstance(loaded["timestamps"], list) and isinstance(loaded["data"], list)
    assert r.status_code == 200

def test_unregister() -> None:
    r = requests.get(SERVER + "/recall")
    assert r.status_code == 200

if (__name__ == "__main__"):
    # pytest should not run this
    pass
