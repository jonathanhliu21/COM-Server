#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import com_server
import pytest
from flask_restful import Resource

def test_endpointexistsexception() -> None:
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
    

def test_subclass_type_exception() -> None:
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

def test_duplicate_class_no_exception() -> None:
    """
    Tests if duplicate class names lead to exceptions
    """
    
    conn = com_server.Connection(115200, "/dev/ttyUSB0")
    handler = com_server.RestApiHandler(conn)

    @handler.add_endpoint("/hello_world")
    def hello_world_test(conn):
        class Hello_World_(com_server.ConnectionResource):
            def get(self):
                return {"hello": "world"}
    
        return Hello_World_
    
    @handler.add_endpoint("/hello_world_2")
    def hello_world_2_test(conn):
        class Hello_World_(com_server.ConnectionResource):
            def get(self):
                return {"hello": "world2"}
        
        return Hello_World_
    
    for e, r in handler.all_endpoints: 
        handler.api.add_resource(r, e)
    
    assert len(handler.all_endpoints) == 2

def test_duplicate_func_name_no_exception() -> None:
    """
    Tests if functions of the same name will lead to exceptions
    """

    conn = com_server.Connection(115200, "/dev/ttyUSB0")
    handler = com_server.RestApiHandler(conn)

    @handler.add_endpoint("/hello_world")
    def hello_world_test(conn):
        class Hello_World_(com_server.ConnectionResource):
            def get(self):
                return {"hello": "world"}
    
        return Hello_World_
    
    @handler.add_endpoint("/hello_world_2")
    def hello_world_test(conn):
        class Hello_World_(com_server.ConnectionResource):
            def get(self):
                return {"hello": "world2"}
        
        return Hello_World_
    
    for e, r in handler.all_endpoints: 
        handler.api.add_resource(r, e)
    
    assert len(handler.all_endpoints) == 2

if (__name__ == "__main__"):
    # pytest should not run this

    conn = com_server.Connection(115200, "/dev/ttyUSB0")
    handler = com_server.RestApiHandler(conn)

    @handler.add_endpoint("/hello_world")
    def hello_world_test(conn):
        class Hello_World_(com_server.ConnectionResource):
            def get(self):
                return {"hello": "world"}
    
        return Hello_World_
    
    @handler.add_endpoint("/hello_world_2")
    def hello_world_2_test(conn):
        class Hello_World_(com_server.ConnectionResource):
            def get(self):
                return {"hello": "world2"}
        
        return Hello_World_
    
    handler.run_dev(host='0.0.0.0', port=8080)
    