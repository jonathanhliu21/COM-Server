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

try:
    requests.get("http://0.0.0.0:8080")
except requests.exceptions.ConnectionError:
    pytestmark = pytest.mark.skip(reason="Server not launched. Make sure it is running on 0.0.0.0 with port 8080")

