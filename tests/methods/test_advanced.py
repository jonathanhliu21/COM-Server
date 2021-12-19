#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests more advanced methods in `Connection` object by using the API,
which are `get_first_response()`, `wait_for_response()`, and `send_for_response()`
"""

import json
import time

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

class TestAdvanced:
    def test_get_first_response(self):
        """
        Tests `/send/get_first`
        """

        send_time = time.time()
        data = {
            "data": [1, 2, 3, 4, send_time],
            "ending": "\n",
            "concatenate": ";"
        }

        r = requests.post(SERVER+"/send/get_first", data=data)
        r2 = requests.post(SERVER+"/send/get_first", data=data)

        time.sleep(1) # send interval; put before assertions to make sure the send interval passes

        # r2 is less than send interval
        assert r2.status_code == 502

        # response should be 200
        loaded = json.loads(r.text)
        assert r.status_code == 200 

        # response should match 
        s = f"Got: \"1;2;3;4;{send_time}\""
        assert loaded["data"] == s

    
    def test_wait_for_response(self):
        """
        Tests /get/wait
        """

        # send data
        send_time = time.time()
        data = {
            "data": [5, 6, 7, 8, send_time],
            "ending": "\n",
            "concatenate": ";"
        }

        requests.post(SERVER+"/send", data=data)

        # wait for sent data
        s = f"Got: \"5;6;7;8;{send_time}\""
        # post request data to get back endpoint
        data_get_back = {
            "response": s,
            "strip": True
        }
        r = requests.post(SERVER+"/get/wait", data=data_get_back)

        time.sleep(1) # send interval; put before assertions to make sure the send interval passes

        assert r.status_code == 200
    
    def test_send_for_response(self):
        """
        /send/get
        """

        s = f"abcd{time.time()}"
        data= {
            "response": f"Got: \"{s}\"",
            "data": s,
            "ending": '\n',
            "strip": True
        }

        data_fail = {
            "response": f"something else",
            "data": s,
            "ending": '\n',
            "strip": True
        }

        r = requests.post(SERVER+"/send/get", data=data)
        r2 = requests.post(SERVER+"/send/get", data=data_fail)

        time.sleep(1) # send interval; put before assertions to make sure the send interval passes

        assert r.status_code == 200
        assert r2.status_code == 502

def test_unregister() -> None:
    r = requests.get(SERVER + "/recall")
    assert r.status_code == 200
