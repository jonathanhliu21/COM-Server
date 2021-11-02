#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time

import com_server
import pytest
from flask_restful import Resource


@pytest.mark.skip(reason="No way of testing without infinite loop")
def test_server_start():
    conn = com_server.Connection(115200, "/dev/ttyUSB0")
    serve = com_server.Base_Rest_Connection(conn)

    @serve.add_endpoint("/test")
    def endpt(obj):
        class TestEndpt(Resource):
            def get(self):
                obj.send(f"sent: {time.time()}")
                a = obj.get(str)
                print(a)
                return {"test": "OK", "rcv": a}

        print(isinstance(TestEndpt, Resource))

        return TestEndpt

    serve.run(host="0.0.0.0", port=8080)


if (__name__ == "__main__"):
    test_server_start()
