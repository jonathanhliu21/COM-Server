#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from com_server import all_ports
import requests
import json
import pytest
import time

SERVER = "http://127.0.0.1:8080/v1"

class Test_All_Ports:
    """tests that /all_ports working properly"""

    @pytest.fixture
    def example_data(self):
        return {
            "data": [1, 2, 3, 4, time.time()],
            "ending": "\n",
            "concatenate": ";"
        }

    res = f"{SERVER}/all_ports"

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
    
    def test_all_ports_working(self):
        """Tests that actual thing is working"""
    
        r = requests.get(self.res)
        loaded = json.loads(r.text)

        assert r.status_code == 200 and loaded["message"] == "OK"

        allp = all_ports()
        cnt = 0

        p = loaded['ports']

        for a, b, c in allp:
            assert a == p[cnt][0]
            assert b == p[cnt][1]
            assert c == p[cnt][2]

            cnt += 1
