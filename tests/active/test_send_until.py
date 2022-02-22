#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import pytest
import time

SERVER = "http://127.0.0.1:8080/v1"

class Test_Send_Until:
    """Tests the /send_until resource"""

    @pytest.fixture
    def example_data(self):
        curt = time.time()
        return {
            "response": f"Got: \"1;2;3;4;{curt}\"",
            "data": [1, 2, 3, 4, curt],
            "ending": "\n",
            "concatenate": ";"
        }

    res = f"{SERVER}/send_until"

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
    
    def test_send_for_response(self, example_data):
        """tests that /send_until is working properly"""

        r = requests.post(self.res, data=example_data)
        loaded = json.loads(r.text)

        assert r.status_code == 200 and loaded['message'] == "OK"
        assert self.example_data_same(loaded['data'], example_data)

        time.sleep(1)    

    def test_send_interval(self, example_data):
        """tests that send interval is working properly"""

        r = requests.post(self.res, data=example_data)
        r = requests.post(self.res, data=example_data)
        loaded = json.loads(r.text)

        assert r.status_code == 200 and loaded['message'] != "OK"

        time.sleep(1)

    def example_data_same(self, d1, d2):
        ret = d1['ending'] == d2['ending'] and d1['concatenate'] == d2['concatenate']
        ret = ret and d1['response'] == d2['response']
        
        if len(d1['data']) != len(d2['data']):
            return False

        for i in range(0, len(d1['data'])):
            ret = ret and str(d1['data'][i]) == str(d2['data'][i])
        
        return ret

