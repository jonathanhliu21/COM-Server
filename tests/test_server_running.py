#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
For testing things with server running. 
Make sure server is running on local computer with host "0.0.0.0" and port "8080" before testing.
"""

import glob
import json
import re
import sys
import time

import pytest
import requests

SERVER = "http://0.0.0.0:8080"

# don't start unless running
try:
    requests.get(SERVER+"/recall")
except requests.exceptions.ConnectionError:
    pytestmark = pytest.mark.skip(
        reason="Server not launched. Make sure it is running on 0.0.0.0 with port 8080, or run \"com_server -p <port> -b <baud> run\".")


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

@pytest.mark.skip(reason="No way of testing without delaying; test manually")
def _test_get() -> None:
    # tests get req; pytest should not run

    data = {
        "data": f"sent at: {time.time()}",
        "ending": "\n",
    }

    r = requests.post(SERVER+"/send", data=data) 
    print(r.text)
    
    r = requests.get(SERVER + "/get")
    print("get:", r.text, data)

    loaded = json.loads(r.text)
    assert r.status_code == 200
    assert loaded["message"] == "OK"

@pytest.mark.skip(reason="No way of testing without delaying; test manually")
def _test_get_first():
    # tests get first; pytest should not run

    data = {
        "data": f"sent at: {time.time()}",
        "ending": "\n",
        "concatenate": ";",
        "strip": True
    }

    r = requests.post(SERVER+"/send/get_first", data=data) 
    print(r.text, data)

@pytest.mark.skip(reason="No way of testing without delaying; test manually")
def _test_wait():
    """NOTE: This only works with a certain program on the Arduino. Program in examples directory."""
    # tests get first; pytest should not run

    data = {
        "data": f"sent at: {time.time()}",
        "ending": "\n",
        "concatenate": ";",
    }
 
    r = requests.post(SERVER+"/send", data=data) 
    print(r.text) 

    data2 = {
        "response": f"Got: \"{data['data']}\"",
        "strip": True
    }

    r = requests.post(SERVER+"/get/wait", data=data2)
    print(r.text)

@pytest.mark.skip(reason="No way of testing without delaying; test manually")
def _test_send_response():
    """NOTE: This only works with a certain program on the Arduino. Program in examples directory."""
    # tests get first; pytest should not run

    t = time.time()
    data = {
        "response": f"Got: \"sent at: {t}\"",
        "data": f"sent at: {t}",
        "ending": '\n',
        "concatenate": ";",
        "strip": True
    }

    r = requests.post(SERVER+"/send/get", data=data)
    print(r.text)


if (sys.platform.startswith("linux")):
    _usb = glob.glob("/dev/ttyUSB[0-9]*")
    _acm = glob.glob("/dev/ttyACM[0-9]*")
    MATCH = "/dev/ttyUSB[0-9]*|/dev/ttyACM[0-9]*"
elif (sys.platform.startswith("darwin")):
    _usb = glob.glob("/dev/cu.usbserial*")
    _acm = []
    MATCH = "/dev/cu.usbserial.*"
else:
    # platform not supported for the test
    _usb = []
    _acm = []

@pytest.mark.skipif(len(_usb+_acm) <= 0, reason="port not connected")
def test_ports_server() -> None:

    r = requests.get(SERVER+"/list_ports")
    loaded = json.loads(r.text)

    matched = False
    for i in loaded["ports"]:
        if (re.match(MATCH, i[0])):
            matched = True
            break

    assert matched

def test_connected() -> None:
    r = requests.get(SERVER+"/connected")
    loaded = json.loads(r.text)
    print(loaded)
    assert r.status_code == 200 and "connected" in loaded

def test_unregister() -> None:
    r = requests.get(SERVER + "/recall")
    assert r.status_code == 200

if (__name__ == "__main__"):
    # pytest should not run this; manual tests
    test_register()

    # write manual tests here
    
    # maps args to functions to test
    test_d = {
        "get": _test_get_first,
        "get_first": _test_get_first,
        "wait": _test_wait,
        "sendres": _test_send_response
    }

    if (len(sys.argv) > 1 and sys.argv[1] in test_d):
        test_d[sys.argv[1]]()

    # end write manual tests

    test_unregister()
