#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Start development server for test_server_running.py
"""

import com_server

if (__name__ == "__main__"):

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
    
    handler.run(host='0.0.0.0', port=8080)
    
