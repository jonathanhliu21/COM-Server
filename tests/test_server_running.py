#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
For testing things with server running. 
Make sure server is running on local computer with host "0.0.0.0" and port "8080" before testing.
"""

import os

import pytest
import requests
from com_server import (BaseConnection, Connection, ConnectionResource,
                        RestApiHandler)

SERVER = "http://0.0.0.0:8080"

try:
    requests.get(SERVER)
except requests.exceptions.ConnectionError:
    pytestmark = pytest.mark.skip(reason="Server not launched. Make sure it is running on 0.0.0.0 with port 8080, or run \"python3 tests/start_server.py\".")

requests.get(SERVER+"/recall")

def test_register() -> None:
    r = requests.get(SERVER + "/register")
    assert r.status_code == 200

def test_unregister() -> None:
    r = requests.get(SERVER + "/recall")
    assert r.status_code == 200
