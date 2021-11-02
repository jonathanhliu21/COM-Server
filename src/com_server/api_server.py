# /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This file contains the implementation to the HTTP server that serves
the web API for the Serial port.
"""

import typing as t

from flask import Flask
from flask_restful import Api, Resource, reqparse

from . import base_connection, connection


class EndpointExistsException(Exception):
    pass


class Base_Rest_Connection:
    """Base class for Rest connections; custom connection classes should extend this class.
    """

    def __init__(self, conn: t.Union[connection.Connection, t.Type[base_connection.BaseConnection]]) -> None:
        """Constructor

        This class contains the `add_endpoint()` decorator that adds 
        API endpoints and the `flask_restful` nested classes. It also
        contains the `run()` function that will gather all endpoints
        and nested classes into `flask_restful` and start the Flask app.

        If you want custom endpoints that do custom things with a `Connection`
        object, then you need a class that extends this class which contains 
        methods that have the `add_endpoint` decorator with the endpoint. 
        The method needs a parameter with the connection object and a nested class 
        that is implemented like the `flask_restful` classes. See [here](https://flask-restful.readthedocs.io)
        for more info on how to implement those classes and `flask_restful`
        in general. 

        Note that the functions cannot have methods `__init__()`,
        as that is reserved for initalizing with a connection object
        as a parameter, `add_endpoint()` or `run()` as those are in the base class.
        """

        self.conn = conn  # assign conn as self

        # flask stuff
        self.app = Flask(__name__)
        self.api = Api(self.app)

        # other
        self.all_endpoints = []  # contains tuple objects (endpoint, class)

    def add_endpoint(self, endpoint: str) -> t.Callable:
        """A decorator with an endpoint argument that indicates what `flask_restful` object to add.

        Use this decorator for a function that contains 
        a `flask_restful` object to add. The function needs to 
        have an argument that takes in the `Connection` object.
        It needs to have a nested class that is implemented like the
        `flask_restful` classes. For more information, see link below.
        Then, it needs to return the class.
        The only argument for this decorator is the endpoint.

        Parameters:
        - `endpoint`: the endpoint of the class. Needs to be formatted using `flask_restful` way.
        See [here](https://flask-restful.readthedocs.io) for more info on formatting and `flask_restful`
        in general.
        """

        def _check_hasalready(add: tuple) -> None:
            """Checks if endpoint exists. If so, raises exception.
            """

            endpt_str = [i for i, _ in self.all_endpoints]
            if (add[0] in endpt_str):
                # endpoint already exists
                raise EndpointExistsException(
                    f"Endpoint {add[0]} already exists")

        def _outer(func: t.Callable) -> t.Callable:
            """Actual decorator that adds to list of functions.
            """

            # func(self.conn) will throw error if parameter is not there
            # checks for return type and if endpoint exists.
            # other errors will be thrown in flask_restful
            # appends (endpoint, class)
            ret = func(self.conn)
            add = (str(endpoint), ret)

            _check_hasalready(add)  # check if endpoint exists already

            if (Resource not in ret.__bases__):
                # if not resource object extend
                raise TypeError(
                    "method needs to return something that extends flask_restful Resource object")

            # append
            self.all_endpoints.append(add)

            return func

        return _outer

    def run(self, **kwargs) -> None:
        """Runs the server

        Calling this begins the connection with the Serial port and calls `Flask.run()`. 
        All arguments provided will be passed to `Flask.run()`.

        Some parameters:
        - `host`: The host of the server. Ex: `localhost`, `0.0.0.0`, `127.0.0.1`, etc.
        - `port`: The port to host it on. Ex: `5000` (default), `8000`, `8080`, etc.
        - `debug`: 

        For more information, see [here](https://flask.palletsprojects.com/en/2.0.x/api/#flask.Flask.run).
        For documentation on Flask in general, see [here](https://flask.palletsprojects.com/en/2.0.x/)
        """

        # connect serial port
        self.conn.connect()

        # add resources to flask_restful
        for name, resource in self.all_endpoints:
            self.api.add_resource(resource, name)

        # Flask run
        self.app.run(**kwargs)

        # disconnect afterwards
        self.conn.disconnect()
