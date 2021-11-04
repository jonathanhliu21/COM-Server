# /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This file contains the implementation to the HTTP server that serves
the web API for the Serial port.
"""

import typing as t

import flask
import flask_restful

from . import base_connection, connection # for typing


class EndpointExistsException(Exception):
    pass

class ConnectionResource:
    """A custom resource object that is built to be used with `RestApiHandler`.

    This class is to be extended and used like the `Resource` class.
    Have `get()`, `post()`, and other methods for the types of responses you need.
    """

    # functions will be implemented in subclasses

class RestApiHandler:
    """A handler for creating endpoints with the `Connection` and `Connection`-based objects.
    
    This class provides the framework for adding custom endpoints for doing
    custom things with the serial connection and running the local server
    that will host the API. It uses a `flask_restful` object as its back end. 

    Note that only one connection (one IP address) will be allowed to connect
    at a time because the serial port can only handle one process. 
    Additionally, endpoints cannot include `/register` or `recall`, as that 
    will be used to ensure that there is only one connection at a time. Finally,
    resource classes have to extend the custom `ConnectionResource` class
    from this library, not the `Resource` from `flask_restful`.
    """

    def __init__(self, conn: t.Union[t.Type[base_connection.BaseConnection], t.Type[connection.Connection]], include_builtins: bool = True, **kwargs) -> None:
        """Constructor for class

        Parameters:
        - `conn` (`Connection`): The `Connection` object the API is going to be associated with. 
        - `include_builtins` (bool) (optional): If the built-in endpoints should be included. If True, then 
        those endpoints cannot be used as custom endpoints. By default True. The built-in endpoints include:
            - `/register` (GET): An endpoint to register an IP; other endpoints will result in `400` status code
            if they are accessed without accessing this first; if an IP is already registered then this will
            result in `400`; IPs must call this first before accessing serial port 
            - `/recall` (GET): After registered, can call `/recall` to "free" IP from server, allowing other IPs to 
            call `/register` to use the serial port
            - `/send` (POST): Send something through the serial port using `Connection.send()` with parameters in request; equivalent to `Connection.send()`
            - `/receive` (GET): Respond with the most recent received string from the serial port; equivalent to `Connection.receive_str()`
            - `/get` (GET): Respond with the first string from serial port after request; equivalent to `Connection.get(str)`
            - `/send/get_first` (POST): Responds with the first string response from the serial port after sending data, with data and parameters in request; equivalent to `Connection.get_first_response()`
            - `/get/wait` (POST): Waits until connection receives string data given in request; different response for success and failure; equivalent to `Connection.wait_for_response()`
            - `/send/get` (POST): Continues sending something until connection receives data given in request; different response for success and failure; equivalent to `Connection.send_for_response()`
            - `/list_ports` (GET): Lists all available Serial ports
        
        Note that `/register` and `/recall` is reserved and cannot be used, even if `include_builtins` is False.
        - `**kwargs`, will be passed to `flask_restful.Api()`
        """

        # from above
        self.conn = conn
        self.include_builtins = include_builtins

        # flask, flask_restful
        self.app = flask.Flask(__name__)
        self.api = flask_restful.Api(self.app, **kwargs)

        # other
        self.all_endpoints = [] # list of all endpoints in tuple (endpoint str, resource class)
        self.registered = False
    
    def add_endpoint(self, endpoint: str) -> t.Callable:
        """Decorator that adds an endpoint

        This decorator needs to go above a function which
        contains a nested class that extends `ConnectionResource`.
        The function needs a parameter indicating the serial connection.
        The function needs to return that nested class.
        The class should contain implementations of request
        methods such as `get()`, `post()`, etc. similar to the 
        `Resource` class from `flask_restful`.

        For more information, see the `flask_restful` [documentation](https://flask-restful.readthedocs.io).

        Note that duplicate endpoints will result in an exception.

        Parameters:
        - `endpoint`: The endpoint to the resource. Cannot repeat.
        Built-in endpoints such as `/send` and `/receive` (see list in `self.__init__()`)
        cannot be used if `include_builtins` is True. Doing so will result in error.
        `/register` and `/recall` cannot be used at all, even if `include_builtins` is False.
        """

        def _checks(resource: t.Any) -> None:
            """Checks endpoint and resource"""

            # check if endpoint exists already
            check = [i for i, _ in self.all_endpoints] 
            if (endpoint in check):
                raise EndpointExistsException(f"Endpoint \"{endpoint}\" already exists")
            
            # check if resource is subclass of ConnectionResource
            if (not issubclass(resource, ConnectionResource)):
                raise TypeError("resource has to extend com_server.ConnectionResource")

        def _outer(func: t.Callable) -> t.Callable:
            """Decorator"""

            resource = func(self.conn) # get resource function

            # checks
            _checks(resource) # will raise exception if fails

            class Res(flask_restful.Resource):
                """The true flask_restful resource object; checks if connected before handling request."""

                # see if resource has attributes and makes new responses
                if (hasattr(resource, "get")):
                    def get(_self, *args, **kwargs):
                        if (not self.registered):
                            # respond with 400 if not registered
                            flask_restful.abort(400, message="Not registered; only one connection at a time")
                        else:
                            return resource.get(**args, **kwargs)
                    
                if (hasattr(resource, "post")):
                    def post(_self, *args, **kwargs):
                        if (not self.registered):
                            # respond with 400 if not registered
                            flask_restful.abort(400, message="Not registered; only one connection at a time")
                        else:
                            return resource.post(**args, **kwargs)
                
                if (hasattr(resource, "head")):
                    def head(_self, *args, **kwargs):
                        if (not self.registered):
                            # respond with 400 if not registered
                            flask_restful.abort(400, message="Not registered; only one connection at a time")
                        else:
                            return resource.head(**args, **kwargs)

                if (hasattr(resource, "put")):
                    def put(_self, *args, **kwargs):
                        if (not self.registered):
                            # respond with 400 if not registered
                            flask_restful.abort(400, message="Not registered; only one connection at a time")
                        else:
                            return resource.put(**args, **kwargs)
                
                if (hasattr(resource, "delete")):
                    def delete(_self, *args, **kwargs):
                        if (not self.registered):
                            # respond with 400 if not registered
                            flask_restful.abort(400, message="Not registered; only one connection at a time")
                        else:
                            return resource.delete(**args, **kwargs)
                
            # append to list of all endpoints
            self.all_endpoints.append((endpoint, resource))

            return func
        
        return _outer
    
    def run(self, **kwargs) -> None:
        """Launches the Flask app.

        All arguments in `**kwargs` will be passed to `Flask.run()`.
        For more information, see [here](https://flask.palletsprojects.com/en/2.0.x/api/#flask.Flask.run).
        For documentation on Flask in general, see [here](https://flask.palletsprojects.com/en/2.0.x/)

        Some arguments include: 
        - `host`: The host of the server. Ex: `localhost`, `0.0.0.0`, `127.0.0.1`, etc.
        - `port`: The port to host it on. Ex: `5000` (default), `8000`, `8080`, etc.
        - `debug`: If the app should be used in debug mode. 
        """

        self.conn.connect() # connection Connection obj

        self.app.run(**kwargs) 

        self.conn.disconnect() # disconnect if stop running
