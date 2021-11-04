#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time

import com_server
import pytest
from flask_restful import Resource

def test_endpointexistsexception():
    """
    Tests if EndpointExistsException is being thrown
    """

    conn = com_server.Connection(115200, "/dev/ttyUSB0")
    handler = com_server.RestApiHandler(conn)

    @handler.add_endpoint("/test1")
    def test1(conn):
        class Test1(com_server.ConnectionResource):
            pass

        return Test1

    # should raise EndpointExistsException
    with pytest.raises(com_server.api_server.EndpointExistsException) as e:
        @handler.add_endpoint("/test1")
        def test2(conn):
            class Test1(com_server.ConnectionResource):
                pass

            return Test1

    ex = e.value
    assert isinstance(ex, com_server.api_server.EndpointExistsException)
    

def test_subclass_type_exception():
    """
    Tests if exception is being thrown if subclass extends wrong type
    """

    conn = com_server.Connection(115200, "/dev/ttyUSB0")
    handler = com_server.RestApiHandler(conn)

    # should raise TypeError
    with pytest.raises(TypeError) as e:
        @handler.add_endpoint("/test2")
        def test2(conn):
            class Test1(Resource):
                pass

            return Test1
    
    ex = e.value
    assert isinstance(ex, TypeError)
