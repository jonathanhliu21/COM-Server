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
    class Test1(com_server.ConnectionResource):
        pass

    # should raise EndpointExistsException
    with pytest.raises(com_server.api_server.EndpointExistsException) as e:

        @handler.add_endpoint("/test1")
        class Test1(com_server.ConnectionResource):
            pass

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
        class Test1(Resource):
            pass

    ex = e.value
    assert isinstance(ex, TypeError)


def test_duplicate_class_no_exception() -> None:
    """
    Tests if duplicate class names lead to exceptions
    """

    conn = com_server.Connection(115200, "/dev/ttyUSB0")
    handler = com_server.RestApiHandler(conn)

    @handler.add_endpoint("/hello_world")
    class Hello_World_(com_server.ConnectionResource):
        def get(self):
            return {"hello": "world"}

    @handler.add_endpoint("/hello_world_2")
    class Hello_World_(com_server.ConnectionResource):
        def get(self):
            return {"hello": "world2"}

    for e, r in handler._all_endpoints:
        handler._api.add_resource(r, e)

    assert len(handler._all_endpoints) == 2


def test_duplicate_func_name_no_exception() -> None:
    """
    Tests if functions of the same name will lead to exceptions
    """

    conn = com_server.Connection(115200, "/dev/ttyUSB0")
    handler = com_server.RestApiHandler(conn)

    @handler.add_endpoint("/hello_world")
    class Hello_World_(com_server.ConnectionResource):
        def get(self):
            return {"hello": "world"}

    @handler.add_endpoint("/hello_world_2")
    class Hello_World_(com_server.ConnectionResource):
        def get(self):
            return {"hello": "world2"}

    for e, r in handler._all_endpoints:
        handler._api.add_resource(r, e)

    assert len(handler._all_endpoints) == 2


if __name__ == "__main__":
    # pytest should not run this

    conn = com_server.Connection(115200, "/dev/ttyUSB0")
    handler = com_server.RestApiHandler(conn)

    @handler.add_endpoint("/hello_world")
    class Hello_World_(com_server.ConnectionResource):
        def get(self):
            return {"hello": "world"}

    class Hello_World_(com_server.ConnectionResource):
        def get(self):
            return {"hello": "world2"}

    handler.run_dev(host="0.0.0.0", port=8080)
