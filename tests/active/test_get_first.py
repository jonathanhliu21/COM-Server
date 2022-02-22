#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import pytest
import time

SERVER = "http://127.0.0.1:8080/v1"

class Test_Get_First:
    """
    tests the /get_first resource
    """

    @pytest.fixture
    def example_data(self):
        return {
            "data": [1, 2, 3, 4, time.time()],
            "ending": "\n",
            "concatenate": ";"
        }

    res = f"{SERVER}/first_response"

    @pytest.mark.parametrize("http_method", [
        requests.get,
        requests.put,
        requests.patch,
    ])
    def test_http_method_with_data(self, example_data, http_method):
        """Tests that only given request works (also tests that HTTP methods are working)"""

        r = http_method(self.res, example_data)
        assert r.status_code == 405
    
    @pytest.mark.parametrize("http_method", [
        requests.delete
    ])
    def test_http_method_no_data(self, http_method):
        """Tests that only given request works (but with options, head, delete requests)"""

        r = http_method(self.res)
        assert r.status_code == 405 
    
    def test_get_first_working(self, example_data):
        """Tests that /first_response is working"""

        curt = example_data["data"][4]

        r = requests.post(self.res, data=example_data)
        loaded = json.loads(r.text)

        assert r.status_code == 200 and loaded["message"] == "OK"
        assert loaded["data"] == f"Got: \"1;2;3;4;{curt}\""
 
        time.sleep(1)
    
    def test_send_int_working(self, example_data):
        """Tests that send interval is still working"""

        r = requests.post(self.res, data=example_data)
        r = requests.post(self.res, data=example_data)
        loaded = json.loads(r.text)

        assert r.status_code == 200 and loaded["message"] != "OK"
 
        time.sleep(1)
