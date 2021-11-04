# /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This file contains the implementation to the HTTP server that serves
the web API for the Serial port.
"""

import typing as t

from flask import Flask
from flask_restful import Api, Resource, reqparse

from . import base_connection, connection # for typing


class EndpointExistsException(Exception):
    pass


class BaseRestConnection:
    """Base class for Rest connections; custom connection classes should extend this class.

    This class contains the `add_endpoint()` decorator that adds 
    API endpoints and the `flask_restful` nested classes. It also
    contains the `run()` function that will gather all endpoints
    and nested classes into `flask_restful` and start the Flask app.

    If you want custom endpoints that do custom things with a `Connection`
    object, then you need a class that extends this class which contains 
    methods that have the `add_endpoint` decorator with the endpoint. 
    The method needs a parameter with a declared `connection` object and a nested class 
    that is implemented like the `flask_restful` classes. See [here](https://flask-restful.readthedocs.io)
    for more info on how to implement those classes and `flask_restful`
    in general. The method then needs to return the class.

    Another way you can create custom endpoints is by initializing this
    base class with an endpoint parameter, then adding the `add_endpoint`
    decorator to a function that has a parameter with a declared 
    `connection` object and a nested class that is implemented like
    `flask_restful` classes. See link above for more info. The function then
    needs to return the class.

    Note that the functions cannot have methods `__init__()`,
    as that is reserved for initalizing with a connection object
    as a parameter, `add_endpoint()` or `run()` as those are in the base class.
    """

    def __init__(self, conn: t.Union[connection.Connection, t.Type[base_connection.BaseConnection]]) -> None:
        """Constructor

        Makes a `Base_Rest_Connection` class or a subclass. Make sure
        subclasses do NOT contain an implementation of this function unless
        you know what you are doing.

        Parameters:
        - `conn`: The `Connection` or `BaseConnection`-based object.
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

        When making a subclass, use `self` to refer to this method. 

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

class RestConnection(BaseRestConnection):
    """Class that contains some endpoint implementations of methods of `Connection` class; can also be extended if you want basic functionality along with your functions.

    Note that this class requires a `Connection` class in
    the constructor. `BaseConnection` will NOT work.

    This class can also be an example on how to make
    your custom endpoints.

    The functions and endpoints in this class include:
    - `all_ports()`, `/list_ports`, 'GET': Responds with all available serial ports.
    - `send()`, `/send`, `POST`: Sends data in request with other arguments of `Connection.send()` in the request.
    - `get()`, `/get`, `GET`: Responds with `Connection.get()` with `str` as the return type. Other parameters will be provided in the request.
    - `receive()`, `/receive`, `GET`: Responds with `Connection.receive_str()`. Other parameters will be provided in the request.
    - `send_for_response()`, `/send/response`, `POST`: Sends data given in request until it receives a string that matches the string given in the request from the serial port. Response is different depending on success and failure.
    - `get_first_response()`, `/send/get`, `POST`: Responds with first response from serial port after sending data given in the request. Response is different depending on success and failure.

    By extending this class, make sure to not use any of the endpoints listed above.
    """
    