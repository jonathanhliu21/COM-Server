#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import pytest
import time

SERVER = "http://127.0.0.1:8080/v1"


class Test_Connection_State:
    """tests the /connection_state resources"""

    @pytest.fixture
    def example_data(self):
        return {"data": [1, 2, 3, 4, time.time()], "ending": "\n", "concatenate": ";"}

    res = f"{SERVER}/connection_state"

    @pytest.mark.parametrize(
        "http_method",
        [
            requests.post,
            requests.put,
            requests.patch,
        ],
    )
    def test_http_method_with_data(self, example_data, http_method):
        """Tests that only given request works (also tests that HTTP methods are working)"""

        r = http_method(self.res, example_data)
        assert r.status_code == 405

    @pytest.mark.parametrize("http_method", [requests.delete])
    def test_http_method_no_data(self, http_method):
        """Tests that only given request works (but with options, head, delete requests)"""

        r = http_method(self.res)
        assert r.status_code == 405

    def test_connection_state_working(self):
        """tests that state is working"""

        r = requests.get(self.res)
        loaded = json.loads(r.text)

        assert loaded["message"] == "OK"
        d = loaded["state"]
        assert (
            "connected" in d
            and "timeout" in d
            and "send_interval" in d
            and "available" in d
            and "port" in d
        )

        # should be same arguments if user typed in command in CLI correctly
        assert d["connected"]
        assert d["timeout"] == 1
        assert d["send_interval"] == 1

    def test_availability_working(self, example_data):
        """tests that the 'available' key is working correctly"""

        # get data to reset availability
        requests.get(f"{SERVER}/get")

        r = requests.get(self.res)
        loaded = json.loads(r.text)

        assert loaded["message"] == "OK"
        d = loaded["state"]

        assert d["available"] == 0

        requests.post(f"{SERVER}/send", data=example_data)
        time.sleep(1)
        requests.post(f"{SERVER}/send", data=example_data)
        time.sleep(1)

        r = requests.get(self.res)
        loaded = json.loads(r.text)

        assert loaded["message"] == "OK"
        d = loaded["state"]

        assert d["available"] == 2
