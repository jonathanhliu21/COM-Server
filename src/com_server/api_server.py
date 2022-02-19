# /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This file contains the implementation to the HTTP server that serves
the web API for the Serial port.
"""

import logging
import threading
import typing as t

import flask
import flask_restful
import waitress
from flask_cors import CORS

from . import connection  # for typing
from . import disconnect


class EndpointExistsException(Exception):
    pass


class ConnectionResource(flask_restful.Resource):
    """A custom resource object that is built to be used with `RestApiHandler` and `ConnectionRoutes`.

    This class is to be extended and used like the `Resource` class.
    Have `get()`, `post()`, and other methods for the types of responses you need.
    """

    # typing for autocompletion
    conn: connection.Connection
    other: t.Dict[str, connection.Connection]

    # functions will be implemented in subclasses


class RestApiHandler:
    """A handler for creating endpoints with the `Connection` and `Connection`-based objects.

    This class provides the framework for adding custom endpoints for doing
    custom things with the serial connection and running the local server
    that will host the API. It uses a `flask_restful` object as its back end.

    Note that endpoints cannot have the names `/register` or `/recall`.
    Additionally, resource classes have to extend the custom `ConnectionResource` class
    from this library, not the `Resource` from `flask_restful`.

    `500 Internal Server Error`s will occur with endpoints dealing with the connection
    if the serial port is disconnected. The server will spawn another thread that will
    immediately try to reconnect the serial port if it is disconnected. However, note
    that the receive and send queues will **reset** when the serial port is disconnected.

    If another process accesses an endpoint while another is
    currently being used, then it will respond with
    `503 Service Unavailable`.

    More information on [Flask](https://flask.palletsprojects.com/en/2.0.x/) and [flask-restful](https://flask-restful.readthedocs.io/en/latest/).

    Register and recall endpoints:

    - `/register` (GET): An endpoint to register an IP; other endpoints will result in `400` status code
    if they are accessed without accessing this first (unless `has_register_recall` is False);
    if an IP is already registered then this will result in `400`; IPs must call this first before
    accessing serial port (unless `has_register_recall` is False)
    - `/recall` (GET): After registered, can call `/recall` to "free" IP from server, allowing other IPs to
    call `/register` to use the serial port
    """

    def __init__(
        self,
        conn: connection.Connection,
        has_register_recall: bool = True,
        add_cors: bool = False,
        catch_all_404s: bool = True,
        **kwargs: t.Any,
    ) -> None:
        """Constructor for class

        Parameters:
        - `conn` (`Connection`): The `Connection` object the API is going to be associated with.
        - `has_register_recall` (bool): If False, removes the `/register` and `/recall` endpoints
        so the user will not have to use them in order to access the other endpoints of the API.
        That is, visiting endpoints will not respond with a 400 status code even if `/register` was not
        accessed. By default True.
        - `add_cors` (bool): If True, then the Flask app will have [cross origin resource sharing](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS) enabled. By default False.
        - `catch_all_404s` (bool): If True, then there will be JSON response for 404 errors. Otherwise, there will be a normal HTML response on 404. By default True.
        - `**kwargs`, will be passed to `flask_restful.Api()`. See [here](https://flask-restful.readthedocs.io/en/latest/api.html#id1) for more info.
        """

        # from above
        self._conn = conn
        self._has_register_recall = has_register_recall

        # flask, flask_restful
        self._app = flask.Flask(__name__)
        self._api = flask_restful.Api(
            self._app, catch_all_404s=catch_all_404s, **kwargs
        )

        if add_cors:
            CORS(self._app)

        # other
        self._all_endpoints = (
            []  # list of all endpoints in tuple (endpoint str, resource class)
        )
        self._registered = (
            None  # keeps track of who is registered; None if not registered
        )
        self._lock = (
            threading.Lock()
        )  # for making sure only one thread is accessing Connection obj at a time

        if has_register_recall:
            # add /register and /recall endpoints
            self._api.add_resource(self._register(), "/register")
            self._api.add_resource(self._recall(), "/recall")

    def __repr__(self) -> str:
        """Printing the API object"""

        return (
            f"RestApiHandler<id={hex(id(self))}>"
            f"{{app={self._app}, api={self._api}, conn={self._conn}, "
            f"registered={self._registered}, endpoints={self._all_endpoints}}}"
        )

    def add_endpoint(self, endpoint: str) -> t.Callable:
        """Decorator that adds an endpoint

        This decorator should go above a class that
        extends `ConnectionResource`. The class should
        contain implementations of request methods such as
        `get()`, `post()`, etc. similar to the `Resource`
        class from `flask_restful`. To use the connection
        object, use the `self.conn` attribute of the class
        under the decorator.

        For more information, see the `flask_restful` [documentation](https://flask-restful.readthedocs.io).

        Note that duplicate endpoints will result in an exception.
        If there are two classes of the same name, even in different
        endpoints, the program will append underscores to the name
        until there are no more repeats. For example, if one class is
        named "Hello" and another class is also named "Hello",
        then the second class name will be changed to "Hello_".
        This happens because `flask_restful` interprets duplicate class
        names as duplicate endpoints.

        If another process accesses an endpoint while another is
        currently being used, then it will respond with
        `503 Service Unavailable`.

        Parameters:
        - `endpoint` (str): The endpoint to the resource. Cannot repeat.
        `/register` and `/recall` cannot be used, even if
        `has_register_recall` is False
        """

        def _checks(resource: t.Any) -> None:
            """Checks endpoint and resource"""

            # check if endpoint exists already
            check = [i for i, _ in self._all_endpoints]
            if endpoint in check:
                raise EndpointExistsException(f'Endpoint "{endpoint}" already exists')

            # check that resource is not None, if it is, did not return class
            if resource is None:
                raise TypeError(
                    "function that the decorator is above must return a class"
                )

            # check if resource is subclass of ConnectionResource
            if not issubclass(resource, ConnectionResource):
                raise TypeError("resource has to extend com_server.ConnectionResource")

            # check if resource name is taken, if so, change it (flask_restful interperets duplicate names as multiple endpoints)
            names = [i.__name__ for _, i in self._all_endpoints]
            if resource.__name__ in names:
                s = f"{resource.__name__}"

                while s in names:
                    # append underscore until no matching
                    s += "_"

                resource.__name__ = s

        def _outer(resource: t.Type[ConnectionResource]) -> t.Type:
            # checks; will raise exception if fails
            _checks(resource)

            # assign connection obj
            resource.conn = self._conn

            # req methods; _self is needed as these will be part of class functions
            def _dec(func: t.Callable) -> t.Callable:
                def _inner(_self, *args: t.Any, **kwargs: t.Any) -> t.Any:
                    ip = flask.request.remote_addr

                    if self._has_register_recall and (
                        not self._registered or self._registered != ip
                    ):
                        # respond with 400 if not registered
                        flask_restful.abort(
                            400, message="Not registered; only one connection at a time"
                        )
                    elif self._lock.locked():
                        # if another endpoint is currently being used
                        flask_restful.abort(
                            503,
                            message="An endpoint is currently in use by another process.",
                        )
                    else:
                        with self._lock:
                            val = func(_self, *args, **kwargs)

                    return val

                return _inner

            # replace functions in class with new functions that check if registered
            if hasattr(resource, "get"):
                resource.get = _dec(resource.get)
            if hasattr(resource, "post"):
                resource.post = _dec(resource.post)
            if hasattr(resource, "head"):
                resource.head = _dec(resource.head)
            if hasattr(resource, "put"):
                resource.put = _dec(resource.put)
            if hasattr(resource, "delete"):
                resource.delete = _dec(resource.delete)

            self._all_endpoints.append((endpoint, resource))

            return resource

        return _outer

    def add_resource(self, *args: t.Any, **kwargs: t.Any) -> None:
        """Calls `flask_restful.add_resource`.

        Allows adding endpoints that do not interact with the serial port.

        See [here](https://flask-restful.readthedocs.io/en/latest/api.html#flask_restful.Api.add_resource)
        for more info on `add_resource` and [here](https://flask-restful.readthedocs.io)
        for more info on `flask_restful` in general.
        """

        return self._api.add_resource(*args, **kwargs)

    def run_dev(self, logfile: t.Optional[str] = None, **kwargs: t.Any) -> None:
        """Launches the Flask app as a development server.

        Not recommended because this is slower, and development features
        such as debug mode and restarting do not work most of the time.
        Use `run()` instead.

        Parameters:
        - `logfile` (str, None): The path of the file to log serial disconnect and reconnect events to.
        Leave as None if you do not want to log to a file. By default None.

        All arguments in `**kwargs` will be passed to `Flask.run()`.
        For more information, see [here](https://flask.palletsprojects.com/en/2.0.x/api/#flask.Flask.run).
        For documentation on Flask in general, see [here](https://flask.palletsprojects.com/en/2.0.x/).

        Automatically disconnects the `Connection` object after
        the server is closed.

        Some arguments include:
        - `host`: The host of the server. Ex: `localhost`, `0.0.0.0`, `127.0.0.1`, etc.
        - `port`: The port to host it on. Ex: `5000` (default), `8000`, `8080`, etc.
        - `debug`: If the app should be used in debug mode. Very unreliable and most likely will not work.
        """

        if not self._conn.connected:
            self._conn.connect()  # connect the Connection obj if not connected

        # register all endpoints to flask_restful
        for endpoint, resource in self._all_endpoints:
            self._api.add_resource(resource, endpoint)

        # add disconnect handler, verbose is True
        _logger = logging.getLogger("com_server_dev")
        _disconnect_handler = disconnect.Reconnector(self._conn, _logger, logfile)
        _disconnect_handler.start()

        self._app.run(**kwargs)

        self._conn.disconnect()  # disconnect if stop running

    def run(self, logfile: t.Optional[str] = None, **kwargs: t.Any) -> None:
        """Launches the Flask app as a Waitress production server (recommended).

        Parameters:
        - `logfile` (str, None): The path of the file to log serial disconnect and reconnect events to.
        Leave as None if you do not want to log to a file. By default None.

        All arguments in `**kwargs` will be passed to `waitress.serve()`.
        For more information, see [here](https://docs.pylonsproject.org/projects/waitress/en/stable/arguments.html#arguments).
        For Waitress documentation, see [here](https://docs.pylonsproject.org/projects/waitress/en/stable/).

        Automatically disconnects the `Connection` object after
        the server is closed.

        If nothing is included, then runs on `http://0.0.0.0:8080`
        """

        if not self._conn.connected:
            self._conn.connect()  # connect the Connection obj if not connected

        # register all endpoints to flask_restful
        for endpoint, resource in self._all_endpoints:
            self._api.add_resource(resource, endpoint)

        _logger = logging.getLogger("waitress")

        # add disconnect handler, verbose is False
        _disconnect_handler = disconnect.Reconnector(self._conn, _logger, logfile)
        _disconnect_handler.start()

        waitress.serve(self._app, **kwargs)

        self._conn.disconnect()  # disconnect if stop running

    # backward compatibility
    run_prod = run

    @property
    def flask_obj(self) -> flask.Flask:
        """
        Gets the `Flask` object that is the backend of the endpoints and the server.

        This can be used to modify and customize the `Flask` object in this class.
        """

        return self._app

    @property
    def api_obj(self) -> flask_restful.Api:
        """
        Gets the `flask_restful` API object that handles parsing the classes.

        This can be used to modify and customize the `Api` object in this class.
        """

        return self._api

    def _register(self) -> t.Type[ConnectionResource]:
        """
        Registers an IP to the server. Note that this is IP-based, not
        process based, so if there are multiple process on the same computer
        connecting to this, the server will not be able to detect it and may
        lead to unexpected behavior.

        Method: GET

        Arguments:
            None

        Responses:
        - `200 OK`: `{"message": "OK"}` if successful
        - `400 Bad Request`:
            - `{"message": "Double registration"}` if this endpoint is reached by an IP while it is registered
            - `{"message": "Not registered; only one connection at a time"}` if this endpoint is reached while another IP is registered
        """

        class _Register(ConnectionResource):
            def get(_self) -> dict:
                ip = flask.request.remote_addr

                # check if already registered
                if self._registered:
                    if self._registered == ip:
                        flask_restful.abort(400, message="Double registration")
                    else:
                        flask_restful.abort(
                            400, message="Not registered; only one connection at a time"
                        )

                self._registered = ip

                return {"message": "OK"}

        return _Register

    def _recall(self) -> t.Type[ConnectionResource]:
        """
        Unregisters an IP from a server and allows other IPs to use it.

        Method: GET

        Arguments:
            None

        Responses:
        - `200 OK`: `{"message": "OK}` if successful
        - `400 Bad Request`:
            - `{"message": "Nothing has been registered"}` if try to call without any IP registered
            - `{"message": "Not same user as one in session"}` if called with different IP as the one registered
        """

        class _Recall(ConnectionResource):
            def get(_self) -> dict:
                ip = flask.request.remote_addr

                # check if not registered
                if not self._registered:
                    flask_restful.abort(400, message="Nothing has been registered")

                # check if ip matches
                if ip != self._registered:
                    flask_restful.abort(400, message="Not same user as one in session")

                self._registered = None

                return {"message": "OK"}

        return _Recall
