# /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
New API Server with new class design
"""

import logging
import sys
import threading
import typing as t
from concurrent.futures import ThreadPoolExecutor

import waitress
from flask import Flask
from flask_restful import Api, abort

from .api_server import ConnectionResource
from .base_connection import ConnectException
from .connection import Connection
from .constants import SUPPORTED_HTTP_METHODS
from .disconnect import MultiReconnector


class DuplicatePortException(Exception):
    pass


class ConnectionRoutes:
    """A wrapper for Flask objects for adding routes involving a `Connection` object

    This class allows the user to easily add REST API routes that interact
    with a serial connection by using `flask_restful`.

    When the connection is disconnected, a `500 Internal Server Error`
    will occur when a route relating to the connection is visited.
    A thread will detect this event and will try to reconnect the serial port.
    Note that this will cause the send and receive queues to **reset**.

    If a resource is accessed while it is being used by another process,
    then it will respond with `503 Service Unavailable`.

    More information on [Flask](https://flask.palletsprojects.com/en/2.0.x/) and [flask-restful](https://flask-restful.readthedocs.io/en/latest/).
    """

    def __init__(self, conn: Connection) -> None:
        """Constructor

        There should only be one `ConnectionRoutes` object that wraps each `Connection` object.
        Having multiple may result in an error.

        Note that `conn` needs to be connected when starting
        the server or else an error will be raised.

        Args:
            conn (Connection): The `Connection` object the API is going to be associated with.
        """

        self._conn = conn

        # dictionary of all resource paths mapped to resource classes
        self._all_resources: t.Dict[str, t.Type[ConnectionResource]] = dict()

        # for making sure only one thread is accessing Connection obj at a time
        self._lock = threading.Lock()

    def __repr__(self) -> str:
        """Printing `ConnectionRoutes`"""

        return f"ConnectionRoutes<id={hex(id(self))}>" f"{{Connection={self._conn}}}"

    def add_resource(self, resource: str) -> t.Callable:
        """Decorator that adds a resource

        The resource should interact with the serial port.
        If not, use `Api.add_resource()` instead.

        This decorator works the same as [Api.resource()](https://flask-restful.readthedocs.io/en/latest/api.html#flask_restful.Api.resource).

        However, the class under the decorator should
        not extend `flask_restful.Resource` but
        instead `com_server.ConnectionResource`. This is
        because `ConnectionResource` contains `Connection`
        attributes that can be used in the resource.

        Unlike a resource added using `Api.add_resource()`,
        if a process accesses this resource while it is
        currently being used by another process, then it will
        respond with `503 Service Unavailable`.

        Currently, supported methods are:

        - `GET`
        - `POST`
        - `PUT`
        - `PATCH`
        - `DELETE`
        - `OPTIONS`
        - `HEAD`

        Make sure to put method names in lowercase

        Args:
            endpoint (str): The endpoint to the resource.
        """

        # outer wrapper
        def _outer(
            resource_cls: t.Type[ConnectionResource],
        ) -> t.Type[ConnectionResource]:

            # check if resource is subclass of ConnectionResource
            if not issubclass(resource_cls, ConnectionResource):
                raise TypeError("resource has to extend com_server.ConnectionResource")

            # assign connection obj
            resource_cls.conn = self._conn

            # req methods; _self is needed as these will be part of class functions
            def _dec(func: t.Callable) -> t.Callable:
                def _inner(_self, *args: t.Any, **kwargs: t.Any) -> t.Any:
                    if self._lock.locked():
                        # if another endpoint is currently being used
                        abort(
                            503,
                            message="An endpoint is currently in use by another process.",
                        )
                    elif not _self.conn.connected:
                        # if not connected
                        abort(500, message="Serial port disconnected.")
                    else:
                        with self._lock:
                            val = func(_self, *args, **kwargs)

                    return val

                return _inner

            # replace functions in class with new functions that check if registered
            for method in SUPPORTED_HTTP_METHODS:
                if hasattr(resource_cls, method):
                    meth_attr = getattr(resource_cls, method)
                    setattr(resource_cls, method, _dec(meth_attr))

            self._all_resources[resource] = resource_cls

            return resource_cls

        return _outer

    @property
    def all_resources(self) -> t.Dict[str, t.Type]:
        """
        Returns a dictionary of resource paths mapped
        to resource classes.
        """

        return self._all_resources


def add_resources(api: Api, *routes: ConnectionRoutes) -> None:
    """Adds all resources given in `servers` to the given `Api`.

    This has to be called along with `start_conns()` **before** calling `start_app()` or running a flask app.

    Args:
        api (Api): The `flask_restful` `Api` object that adds the resources
        *routes (ConnectionRoutes): The `ConnectionRoutes` objects to add to the server
    """

    res = [route.all_resources for route in routes]

    for routes_obj in res:
        for endpoint in routes_obj:
            api.add_resource(routes_obj[endpoint], endpoint)


def start_conns(
    logger: logging.Logger, *routes: ConnectionRoutes, logfile: t.Optional[str] = None
) -> None:
    """Initializes serial connections and disconnect handler

    Args:
        *routes (ConnectionRoutes): The `ConnectionRoutes` objects to initialize connections from
        logger (Logger): A python logging object
        logfile (str, None, optional): Path of file to log messages to. Defaults to None.

    Raises:
        DuplicatePortException: If any ports in `ConnectionRoutes` have ports in common
        ConnectException: If any of the connections failed in the `ConnectionRoutes` objects.
    """

    # check no duplicate serial ports
    tot: tuple = tuple()
    for route in routes:
        tot += route._conn._ports_list
    tot_s = set(tot)

    if len(tot) != len(tot_s):
        raise DuplicatePortException(
            "Connection objects cannot have any ports in common"
        )

    # start threads
    def _initializer(route: ConnectionRoutes) -> None:
        if not route._conn.connected:
            route._conn.connect()

    with ThreadPoolExecutor() as executor:
        futures = executor.map(_initializer, routes)

        for _ in futures:
            # prints out errors
            pass

    # check that all connections are connected
    # if not, raise ConnectException
    for route in routes:
        if not route._conn.connected:
            raise ConnectException("Connection failed.")

    conns = (route._conn for route in routes)
    reconnector = MultiReconnector(logger, *conns, logfile=logfile)

    # start disconnect/reconnect thread
    reconnector.start()


def disconnect_conns(*routes: ConnectionRoutes) -> None:
    """Disconnects all `Connection` objects in provided `ConnectionRoutes` objects

    It is recommended to call this after `start_app()` to make sure that the serial
    connections are closed.

    Note that calling this will exit the program using `sys.exit()`.

    Args
        *routes (ConnectionRoutes): The `ConnectionRoutes` objects to disconnect connections from
    """

    for route in routes:
        route._conn.disconnect()

    sys.exit()


def start_app(
    app: Flask,
    api: Api,
    *routes: ConnectionRoutes,
    logfile: t.Optional[str] = None,
    host: str = "0.0.0.0",
    port: int = 8080,
    cleanup: t.Optional[t.Callable] = None,
    **kwargs: t.Any,
) -> None:
    """Starts a waitress production server that serves the app

    Note that connection objects between `ConnectionRoutes`
    can share no ports in common.

    Using this is recommended over calling `add_resources()`,
    `start_conns()`, `serve_app()`, and `disconnect_conns()`
    separately.

    **Also note that adding multiple `ConnectionRoutes` is
    not tested and may result in very unexpected behavior
    when disconnecting and reconnecting**.

    Lastly, note that `sys.exit()` will be called in this,
    so add any cleanup operations to the `cleanup` parameter.

    Args:
        app (Flask): The flask object that runs the server
        api (Api): The flask_erstful API object that adds the resources
        *routes (ConnectionRoutes): The `ConnectionRoutes` objects to add to the server
        logfile (str, None, optional): The path to the file to log serial disconnect/reconnect events to \
        Leave as None if you do not want to log to a file. Defaults to None.
        host (str, optional): The host of the server (e.g. 0.0.0.0 or 127.0.0.1). Defaults to "0.0.0.0".
        port (int, optional): The port to host the server on (e.g. 8080, 8000, 5000). Defaults to 8080.
        cleanup (Callable, optional): Cleanup function to be called after waitress is done serving app. Defaults to None.
        **kwargs (Any): will be passed to `waitress.serve()`
    """
    # initialize app by adding resources and staring connections and disconnect handlers
    add_resources(api, *routes)

    # get waitress logger
    _logger = logging.getLogger("waitress")
    start_conns(_logger, *routes, logfile=logfile)

    # serve on waitress
    waitress.serve(app, host=host, port=port, **kwargs)

    # call cleanup function
    if cleanup:
        cleanup()

    # destroy connection objects and exit the program
    disconnect_conns(*routes)
