#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import pytest
import time

SERVER = "http://127.0.0.1:8080/v1"


class Test_Send:
    """
    Tests the /send resource
    """

    res = f"{SERVER}/send"

    @pytest.fixture
    def example_data(self):
        return {"data": [1, 2, 3, 4, time.time()], "ending": "\n", "concatenate": ";"}

    @pytest.mark.parametrize(
        "http_method",
        [
            requests.get,
            requests.put,
            requests.patch,
        ],
    )
    def test_http_method_with_data(self, example_data, http_method):
        """Tests that only POST request works (also tests that HTTP methods are working)"""

        r = http_method(self.res, example_data)
        assert r.status_code == 405

    @pytest.mark.parametrize("http_method", [requests.delete])
    def test_http_method_no_data(self, http_method):
        """Tests that only POST request works (but with options, head, delete requests)"""

        r = http_method(self.res)
        assert r.status_code == 405

    def test_format_correctly(self):
        """Tests that 400 if formatted improperly"""

        r = requests.post(self.res, {"aa": 5})
        assert r.status_code == 400

    def test_work_normally(self, example_data):
        """Tests that sending works normally"""

        r = requests.post(self.res, example_data)
        loaded = json.loads(r.text)
        assert r.status_code == 200 and loaded["message"] == "OK"

        assert self.example_data_same(loaded["data"], example_data)

    def test_send_interval_working(self, example_data):
        """Tests that send interval is working normally"""

        r = requests.post(self.res, example_data)
        loaded = json.loads(r.text)
        assert r.status_code == 200 and loaded["message"] != "OK"
        assert "data" not in loaded

        # wait send interval
        time.sleep(1)

        r = requests.post(self.res, example_data)
        loaded = json.loads(r.text)
        assert r.status_code == 200 and loaded["message"] == "OK"
        assert self.example_data_same(loaded["data"], example_data)

        time.sleep(1)

    def example_data_same(self, d1, d2):
        ret = d1["ending"] == d2["ending"] and d1["concatenate"] == d2["concatenate"]

        if len(d1["data"]) != len(d2["data"]):
            return False

        for i in range(0, len(d1["data"])):
            ret = ret and str(d1["data"][i]) == str(d2["data"][i])

        return ret
