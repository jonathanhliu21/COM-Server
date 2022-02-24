#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
An example of how to host the API with `RestApiHandler` and `Builtins`.

Includes examples of how to add the built-in endpoints and how to make
your own endpoints.
"""

from com_server import Connection, ConnectionResource, RestApiHandler
from com_server.api import Builtins

# make the Connection object
conn = Connection(baud=115200, port="/dev/ttyUSB0") # if Linux
# conn = Connection(baud=115200, port="/dev/ttyUSB...") # if Linux; can be "/dev/ttyACM..."
# conn = Connection(baud=115200, port="/dev/cu.usbserial...") # if Mac
# conn = Connection(baud=115200, port="COM...") # if Windows

# make the API Handler object; initialize it with the connection object
handler = RestApiHandler(conn)

# add built-in endpoints, does not need to assign to variable; initialize with handler object
Builtins(handler)

# NOTE: these endpoints CANNOT be used, regardless of adding built-ins or not
# - "/register" (GET) - Used to register an IP, all programs must reach this endpoint before interacting with other endpoints
# - "/recall" (GET) - Used to unregister IP and allow others to access the endpoints

# NOTE: these endpoints CANNOT be used after adding built-ins
# - `/<version>/send` (POST): Send something through the serial port
# - `/<version>/receive` (GET, POST): Respond with the most recent received string from the serial port
# - `/<version>/receive/all` (GET, POST): Returns the entire receive queue
# - `/<version>/get` (GET, POST): Respond with the first string from serial port after request
# - `/<version>/send/get_first` (POST): Responds with the first string response from the serial port after sending data, with data and parameters in request
# - `/<version>/get/wait` (POST): Waits until connection receives string data given in request
# - `/<version>/send/get` (POST): Continues sending something until connection receives data given in request
# - `/<version>/connected` (GET): Indicates if the serial port is currently connected or not
# - `/<version>/list_ports` (GET): Lists all available Serial ports
# where <version> is any supported version of the built-in API.
# See API docs for more details.

# adding a custom endpoint:
@handler.add_endpoint("/hello_world")
class Hello_World_Endpoint(ConnectionResource):
    # classes are implemented like flask_restful classes
    # each method defines a request method (i.e. get() defines what happens when there is a GET request, post() defines what happens when there is a POST request, etc.)
    # to access request parameters, import reqparse from flask_restful (i.e. "from flask_restful import reqparse")
    # to abort a request, import abort from flask_restful (i.e. "from flask_restful import abort")
    # for more information on flask_restful, see https://flask-restful.readthedocs.io/en/latest/
    # for more information on Flask, see https://flask.palletsprojects.com/en/2.0.x/

    def get(self):
        """
        When there is a GET request, this endpoint will respond with

        {
            "Hello": "World!",
            "Received": [timestamp, data]
        }

        The "Received" key is mapped to a value that is a list: [timestamp, data]
        where timestamp is the time that the data was received from the serial port and
        data is the data that came from the serial port.

        However, if there was no data received, then "Received" should be null.
        """

        return {
            "Hello": "World!",
            "Received": self.conn.receive_str()
        }    

# start the Flask development server on http://0.0.0.0:8080 (not recommended because slow)
# handler.run_dev(host="0.0.0.0", port=8080)

# start the waitress production server on http://0.0.0.0:8080
handler.run(host="0.0.0.0", port=8080)

# call disconnect(), as variable will not be used anymore
conn.disconnect()
