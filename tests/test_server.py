#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from com_server import Connection, start_conns, ConnectionRoutes, ConnectionResource, DuplicatePortException
from flask_restful import Resource
import pytest

def test_subclass_type_exception() -> None:
    """
    Tests if exception is being thrown if subclass extends wrong type
    """

    conn = Connection(115200, "/dev/ttyUSB0")
    handler = ConnectionRoutes(conn)

    # should raise TypeError
    with pytest.raises(TypeError) as e:
        @handler.add_resource("/test2")
        class Test1(Resource):
            pass
    
    # no exception
    @handler.add_resource("/test1")
    class Test2(ConnectionResource):
        pass
    
    ex = e.value
    assert isinstance(ex, TypeError)

def test_mult_ports_exception() -> None:
    """
    If any shared ports between connection objects, should raise exception
    """

    conn1 = Connection(115200, "port1", "port2", "port3")
    conn2 = Connection(115200, "port4", "port5", "port6", "port10", "port11", "port12")
    conn3 = Connection(115200, "port3", "port7", "port8", "port9", "port10")

    h1 = ConnectionRoutes(conn1)
    h2 = ConnectionRoutes(conn2)
    h3 = ConnectionRoutes(conn3)
    
    with pytest.raises(DuplicatePortException):
        start_conns(h1, h2, h3)

# below are tests for ConnectionRoutes all_resources dictionary

def test_add_one_route_map_one() -> None:
    """
    Adding one route should result in size 1 and classname being mapped to class
    """

    conn1 = Connection(115200, "port1") 
    h1 = ConnectionRoutes(conn1)

    @h1.add_resource("/abcd")
    class ABCD(ConnectionResource):
        pass

    assert len(h1.all_resources) == 1
    assert h1.all_resources["/abcd"] == ABCD

def test_add_two_route_map_two() -> None:
    """
    Adding two different routes with different classnames should have both in map
    """

    conn1 = Connection(115200, "port1")
    h1 = ConnectionRoutes(conn1)

    @h1.add_resource("/route1")
    class Route1(ConnectionResource):
        pass
    
    @h1.add_resource("/route2")
    class Route2(ConnectionResource):
        pass

    assert len(h1.all_resources) == 2
    assert h1.all_resources["/route1"] == Route1
    assert h1.all_resources["/route2"] == Route2

def test_add_one_route_map_two() -> None:
    """
    Adding one route path to 2 different classnames should result in 2nd classname in map
    """

    conn1 = Connection(115200, "port1")
    h1 = ConnectionRoutes(conn1)

    @h1.add_resource("/route1")
    class Route1(ConnectionResource):
        pass
    
    @h1.add_resource("/route1")
    class Route2(ConnectionResource):
        pass

    assert len(h1.all_resources) == 1
    assert h1.all_resources["/route1"] == Route2

def test_add_two_routes_map_one() -> None:
    """
    Adding two route paths with one classname should result in different class objects
    """

    conn1 = Connection(115200, "port1")
    h1 = ConnectionRoutes(conn1)

    @h1.add_resource("/route1")
    class Route1(ConnectionResource):
        a = 5
    
    @h1.add_resource("/route2")
    class Route1(ConnectionResource):
        # to distinguish which Route1 class
        b = 6
    
    assert len(h1.all_resources) == 2
    assert h1.all_resources["/route1"].a == 5
    assert h1.all_resources["/route2"].b == 6
