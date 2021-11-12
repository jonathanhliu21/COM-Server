#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
An example of how to host the API with `RestApiHandler` and `Builtins`.

Includes examples of how to add the built-in endpoints and how to make
your own endpoints.
"""

from com_server import Builtins, Connection, ConnectionResource, RestApiHandler

# make the Connection object
conn = Connection(baud=115200, port="/dev/ttyUSB0")
# conn = Connection(baud=115200, port="/dev/ttyUSB...") # if Linux; can be "/dev/ttyACM..."
# conn = Connection(baud=115200, port="/dev/cu.usbserial...") 
# conn = Connection(baud=115200, port="COM...") # if Windows

# make the API Handler object; initialize it with the connection object
handler = RestApiHandler(conn)

# add built-in endpoints, does not need to assign to variable; initialize with handler object
Builtins(handler)

# NOTE: these endpoints CANNOT be used, regardless of adding built-ins or not
# - "/register" (GET) - Used to register an IP, all programs must reach this endpoint before interacting with other endpoints
# - "/recall" (GET) - Used to unregister IP and allow others to access the endpoints

# NOTE: these endpoints CANNOT be used after adding built-ins
# - `/send` (POST): Send something through the serial port
# - `/receive` (GET, POST): Respond with the most recent received string from the serial port
# - `/receive/all` (GET, POST): Returns the entire receive queue
# - `/get` (GET, POST): Respond with the first string from serial port after request
# - `/send/get_first` (POST): Responds with the first string response from the serial port after sending data, with data and parameters in request
# - `/get/wait` (POST): Waits until connection receives string data given in request
# - `/send/get` (POST): Continues sending something until connection receives data given in request
# - `/connected` (GET): Indicates if the serial port is currently connected or not
# - `/list_ports` (GET): Lists all available Serial ports

# adding a custom endpoint:
@handler.add_endpoint("/hello_world")
def hello_world(conn: Connection):
    # create a function with a class within it, then return the class

    class Hello_World_Endpoint(ConnectionResource):
        # classes are implemented like flask_restful classes
        # each method defines a request method (i.e. get() defines what happens when there is a GET request, post() defines what happens when there is a POST request, etc.)
        # to access request parameters, import reqparse from flask_restful (i.e. "from flask_restful import reqparse")
        # to abort a request, import abort from flask_restful (i.e. "from flask_restful import abort")
        # for more information on flask_restful, see https://flask-restful.readthedocs.io/en/latest/
        # for more information on Flask, see https://flask.palletsprojects.com/en/2.0.x/

        def get(self):
            return {
                "Hello": "World!",
                "Received": conn.receive_str()
            }
    
    return Hello_World_Endpoint

# start the Flask development server on http://0.0.0.0:8080
handler.run_dev(host="0.0.0.0", port=8080)

# start the waitress production server on http://0.0.0.0:8080
# handler.run_prod(host="0.0.0.0", port=8080)

# call disconnect(), as variable will not be used anymore
conn.disconnect()
