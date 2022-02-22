#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import pytest
import time

SERVER = "http://127.0.0.1:8080/v1"

class Test_Receive:
    """
    tests the /receive and /receive/x resources
    """

    @pytest.fixture
    def example_data(self):
        return {
            "data": [1, 2, 3, 4, time.time()],
            "ending": "\n",
            "concatenate": ";"
        }

    res = f"{SERVER}/receive"

    @pytest.mark.parametrize("http_method", [
        requests.post,
        requests.put,
        requests.patch,
    ])
    def test_http_method_with_data(self, example_data, http_method):
        """Tests that only given request works (also tests that HTTP methods are working)"""

        r = http_method(self.res, example_data)
        assert r.status_code == 405

        r = http_method(f"{self.res}/23", example_data)
        assert r.status_code == 405
    
    @pytest.mark.parametrize("http_method", [
        requests.delete
    ])
    def test_http_method_no_data(self, http_method):
        """Tests that only given request works (but with options, head, delete requests)"""

        r = http_method(self.res)
        assert r.status_code == 405 

        r = http_method(f"{self.res}/23")
        assert r.status_code == 405

    def test_receive_first_good(self, example_data):
        """Tests that the first thing sent is received correctly"""

        curt = example_data["data"][4]

        requests.post(f"{SERVER}/send", data=example_data)
        time.sleep(1);

        r = requests.get(f"{SERVER}/receive/0")
        loaded = json.loads(r.text)

        assert r.status_code == 200 and loaded["message"] == "OK"
        
        assert loaded["data"] == f"Got: \"1;2;3;4;{curt}\""
    
    def test_receive_second_good(self, example_data):
        """Tests that the 2nd most recent received object is correct"""

        curt = example_data["data"][4]

        requests.post(f"{SERVER}/send", data=example_data)
        time.sleep(1);
        requests.post(f"{SERVER}/send", data=example_data)
        time.sleep(1);

        r = requests.get(f"{SERVER}/receive/1")
        loaded = json.loads(r.text)

        assert r.status_code == 200 and loaded["message"] == "OK"
        
        assert loaded["data"] == f"Got: \"1;2;3;4;{curt}\""
        
    
    def test_receive_all(self, example_data):
        """Tests that things are being received in the order they should be"""

        curt = example_data["data"][4]

        requests.post(f"{SERVER}/send", data=example_data)
        time.sleep(1);

        r = requests.get(f"{SERVER}/receive")
        loaded = json.loads(r.text)

        assert r.status_code == 200 and loaded["message"] == "OK"

        assert loaded["data"][-1] == f"Got: \"1;2;3;4;{curt}\""

class Test_Get:
    """
    tests the /get resource 
    """

    @pytest.fixture
    def example_data(self):
        return {
            "data": [1, 2, 3, 4, time.time()],
            "ending": "\n",
            "concatenate": ";"
        }

    res = f"{SERVER}/get"

    @pytest.mark.parametrize("http_method", [
        requests.post,
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
    
    def test_get_working(self, example_data):
        """tests that get works with example data"""

        curt = example_data["data"][4]

        requests.post(f"{SERVER}/send", data=example_data)
        r = requests.get(f"{SERVER}/get")
        loaded = json.loads(r.text)

        assert r.status_code == 200 and loaded["message"] == "OK"
        assert loaded["data"] == f"Got: \"1;2;3;4;{curt}\""

        time.sleep(1)
