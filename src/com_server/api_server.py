#/usr/bin/env python3
# -*- codec: utf-8 -*-

"""
This file contains the implementation to the HTTP server that serves
the web API for the Serial port.
"""

from flask import Flask
from flask_restful import Resource, Api, reqparse

from . import connection


class EndpointExistsException(Exception):
    pass

class Rest_Nested:
    """
    All nested REST classes must extend this in addition to 
    `Resource`. This is used to detect classes for adding endpoints.
    """

class Rest_Connection():
    """The Connection object for HTTP RESTful APIs. 
    Contains resource classes that represent endpoints
    for the API. 
    
    This class only contains the bare endpoints `/send`
    and `/get`. To add more functionality, make a class
    that extends this class. The class needs nested `flask_restful` 
    Resource classes and an `__init__()` that adds these resources 
    and the endpoints by calling `self.add_endpoint()`. Make sure 
    the classes do not match `Send_Endpt()` or `Get_Endpt()` and 
    the endpoints do not match `/send` or `/get`.

    The endpoints for the base class include:
        - `/send`: Sends given string data to Serial port
        - `/get`: Gets string data from Serial port
    
    Call the `run()` method in order to start the server.
    """

    # flask stuff
    app = Flask(__name__)
    api = Api(app)

    all_endpoints = [] # a list of all endpoints to make sure there are no repeats

    def __init__(self) -> None:
        """The Connection object for HTTP RESTful APIs. 
        Contains resource classes that represent endpoints
        for the API. 
        
        This class only contains the bare endpoints `/send`
        and `/get`. To add more functionality, make a class
        that extends this class. The class needs nested `flask_restful` 
        Resource classes and an `__init__()` that adds these resources 
        and the endpoints by calling `self.add_endpoint()`. Make sure 
        the classes do not match `Send_Endpt()` or `Get_Endpt()` and 
        the endpoints do not match `/send` or `/get`.

        The endpoints for the base class include:
            - `/send`: Sends given string data to Serial port
            - `/get`: Gets string data from Serial port
        
        Call the `run()` method in order to start the server.
        """
    
    def add_endpoint(self, endpoint: str) -> None:
        """Adds endpoint given string

        If the endpoint already exists, then raises an exception.

        Parameters:
        - `endpoint` (str): The endpoint to add
        """

        if (endpoint in self.all_endpoints):
            raise EndpointExistsException(f"endpoint {endpoint} already exists")
        
        self.api.add_resource(endpoint)
        self.all_endpoints.append(endpoint)

    def run(self, conn: connection.Connection, **kwargs) -> None:
        """Starts the Serial port connection and runs the API.

        All `**kwargs` will be passed to `flask.Flask.run()`.
        This includes `host`, `port`, etc.

        Parameters:
        - `conn`: The connection object that the class will be interfacing.
        - `**kwargs`: Will be sent to `flask.Flask.run()`
        """

        

        self.app.run(**kwargs)

    class Send_Endpt(Rest_Nested, Resource):
        """Send something given through a POST request.

        Calls `Connection.send()`. If function returns `False` (or failed to send), returns
        `{"status": "FAIL"}`. If it returns `True` (succeeded in sending), returns
        `{"status": "OK"}`.
        """

        def post(self) -> dict:
            """
            Arguments:
            - `send` (list): A list of things to send.
            - `check_type` (bool): If types in `send` should be checked. By default True.
            - `ending` (str): The ending of the bytes object to be sent through the Serial port. By default a carriage return.
            - `concatenate` (str): What the strings in `send` should be concatenated by. By default a space.

            See `Connection.send()` for more details.
            """

            parser = reqparse.RequestParser()
            parser.add_argument("send", type=list, help="A list of things to send", required=True)
            parser.add_argument("check_type", type=bool, help="If types in *args should be checked", default=True)
            parser.add_argument("ending", type=str, help="The ending of the bytes object to be sent through the Serial port", default="\r\n") 
            parser.add_argument("concatenate", type=str, help="What the strings should be concatenated by", default=' ')

            args = parser.parse_args()

            print(args)
    
    class Get_Endpt(Rest_Nested, Resource):
        """Returns the first thing that comes from the Serial port after a GET request.
        """
