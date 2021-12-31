# /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Version 0 of Builtin API. All endpoints below will be prefixed with /v0/ and cannot be used.
"""

import typing as t

import flask_restful
from flask_restful import reqparse

from .. import Connection, ConnectionResource, RestApiHandler, all_ports


class Builtins:
    """Contains implementations of endpoints that call methods of `Connection` object

    Endpoints include:
        - `/v0/send` (POST): Send something through the serial port using `Connection.send()` with parameters in request; equivalent to `Connection.send(...)`
        - `/v0/receive` (GET, POST): Respond with the most recent received string from the serial port; equivalent to `Connection.receive_str(...)`
        - `/v0/receive/all` (GET, POST): Returns the entire receive queue; equivalent to `Connection.get_all_rcv_str(...)`
        - `/v0/get` (GET, POST): Respond with the first string from serial port after request; equivalent to `Connection.get(str, ...)`
        - `/v0/send/get_first` (POST): Responds with the first string response from the serial port after sending data, with data and parameters in request; equivalent to `Connection.get_first_response(is_bytes=False, ...)`
        - `/v0/get/wait` (POST): Waits until connection receives string data given in request; different response for success and failure; equivalent to `Connection.wait_for_response(...)`
        - `/v0/send/get` (POST): Continues sending something until connection receives data given in request; different response for success and failure; equivalent to `Connection.send_for_response(...)`
        - `/v0/connection_state` (GET): Get the properties of the `Connection` object: connected, timeout, send_interval, conn_obj, available, port
        - `/v0/connected` (GET): Indicates if the serial port is currently connected or not
        - `/v0/list_ports` (GET): Lists all available Serial ports
    
    These endpoints cannot be added later.
    """

    def __init__(self, handler: RestApiHandler, verbose: bool = False) -> None:
        """Constructor for class that contains builtin endpoints

        Adds endpoints to given `RestApiHandler` class;
        uses `Connection` object within the class to handle
        serial data.

        Parameters:
        - `handler`: The `RestApiHandler` class that this class should wrap around
        - `verbose`: Prints the arguments each endpoint receives to stdout. Should not be used in production. By default False.
        """

        if not isinstance(handler._conn, Connection):
            raise TypeError(
                "The connection object passed into the handler must be a Connection type"
            )

        self._handler = handler
        self._verbose = verbose

        # version
        self._VERSION = "v0"

        # add all endpoints
        self._add_all()

    def _add_all(self):
        """Adds all endpoints to handler"""

        V = self._VERSION

        # /send
        self._handler.add_endpoint(f"/{V}/send")(self._send())

        # /receive
        self._handler.add_endpoint(f"/{V}/receive")(self._receive())

        # /receive/all
        self._handler.add_endpoint(f"/{V}/receive/all")(self._receive_all())

        # /get
        self._handler.add_endpoint(f"/{V}/get")(self._get())

        # /send/get_first
        self._handler.add_endpoint(f"/{V}/send/get_first")(self._get_first_response())

        # /get/wait
        self._handler.add_endpoint(f"/{V}/get/wait")(self._wait_for_response())

        # /send/get
        self._handler.add_endpoint(f"/{V}/send/get")(self._send_for_response())

        # /connection_state
        self._handler.add_endpoint(f"/{V}/connection_state")(self._connection_state())

        # /connected
        self._handler.add_endpoint(f"/{V}/connected")(self._connected())

        # /list_ports
        self._handler.add_endpoint(f"/{V}/list_ports")(self._list_all())

    # keeping outside wrapper function for documentation
    def _send(_self) -> t.Type[ConnectionResource]:
        """/send"""

        class _Sending(ConnectionResource):
            # make parser once when class is declared, don't add arguments each time request is made aka don't put in post()
            parser = reqparse.RequestParser()
            parser.add_argument(
                "data",
                required=True,
                action="append",
                help="Data the serial port should send; is required",
            )
            parser.add_argument(
                "ending",
                default="\r\n",
                help="Ending that will be appended to the end of data before sending over serial port; default carriage return + newline",
            )
            parser.add_argument(
                "concatenate",
                default=" ",
                help="What the strings in data should be concatenated by if list; by default a space",
            )

            def post(self) -> dict:
                args = self.parser.parse_args(strict=True)

                if _self._verbose:
                    print("Arguments for /send:", args)

                # no need for check_type because everything will be parsed as a string
                res = self.conn.send(
                    *args["data"],
                    ending=args["ending"],
                    concatenate=args["concatenate"]
                )

                if not res:
                    # abort if failed to send
                    flask_restful.abort(502, message="Failed to send")

                return {"message": "OK"}

        return _Sending

    def _receive(_self) -> t.Type[ConnectionResource]:
        """/receive"""

        class _Receiving(ConnectionResource):
            parser = reqparse.RequestParser()
            parser.add_argument(
                "num_before", type=int, default=0, help="Which receive data to return"
            )
            parser.add_argument(
                "read_until",
                default=None,
                help="What character the string should read until",
            )
            parser.add_argument(
                "strip",
                type=bool,
                default=False,
                help="If the string should be stripped of whitespaces and newlines before responding",
            )

            def get(self) -> dict:
                res = self.conn.receive_str()

                return {
                    "message": "OK",
                    "timestamp": res[0] if isinstance(res, tuple) else None,
                    "data": res[1] if isinstance(res, tuple) else None,
                }

            def post(self) -> dict:
                args = self.parser.parse_args(strict=True)

                if _self._verbose:
                    print("Arguments for /receive:", args)

                res = self.conn.receive_str(
                    num_before=args["num_before"],
                    read_until=args["read_until"],
                    strip=args["strip"],
                )

                return {
                    "message": "OK",
                    "timestamp": res[0] if isinstance(res, tuple) else None,
                    "data": res[1] if isinstance(res, tuple) else None,
                }

        return _Receiving

    def _receive_all(_self) -> t.Type[ConnectionResource]:
        """/receive/all"""

        class _ReceiveAll(ConnectionResource):

            parser = reqparse.RequestParser()
            parser.add_argument(
                "read_until",
                default=None,
                help="What character the string should read until",
            )
            parser.add_argument(
                "strip",
                type=bool,
                default=False,
                help="If the string should be stripped of whitespaces and newlines before responding",
            )

            def get(self) -> dict:
                all_rcv = self.conn.get_all_rcv_str()

                return {
                    "message": "OK",
                    "timestamps": [ts for ts, _ in all_rcv],
                    "data": [data for _, data in all_rcv],
                }

            def post(self) -> dict:
                args = self.parser.parse_args(strict=True)

                if _self._verbose:
                    print("Arguments for /receive/all:", args)

                all_rcv = self.conn.get_all_rcv_str(
                    read_until=args["read_until"], strip=args["strip"]
                )

                return {
                    "message": "OK",
                    "timestamps": [ts for ts, _ in all_rcv],
                    "data": [data for _, data in all_rcv],
                }

        return _ReceiveAll

    def _get(_self) -> t.Type[ConnectionResource]:
        """/get"""

        class _Get(ConnectionResource):

            parser = reqparse.RequestParser()
            parser.add_argument(
                "read_until",
                default=None,
                help="What character the string should read until",
            )
            parser.add_argument(
                "strip",
                type=bool,
                default=False,
                help="If the string should be stripped of whitespaces and newlines before responding",
            )

            def get(self) -> dict:
                got = self.conn.get(str)

                if got is None:
                    flask_restful.abort(502, message="Nothing received")

                return {"message": "OK", "data": got}

            def post(self) -> dict:
                args = self.parser.parse_args(strict=True)

                if _self._verbose:
                    print("Arguments for /get:", args)

                got = self.conn.get(
                    str, read_until=args["read_until"], strip=args["strip"]
                )

                if got is None:
                    flask_restful.abort(502, message="Nothing received")

                return {"message": "OK", "data": got}

        return _Get

    def _get_first_response(_self) -> t.Type[ConnectionResource]:
        """/send/get_first"""

        class _GetFirst(ConnectionResource):

            parser = reqparse.RequestParser()

            parser.add_argument(
                "data",
                required=True,
                action="append",
                help="Data the serial port should send; is required",
            )
            parser.add_argument(
                "ending",
                default="\r\n",
                help="Ending that will be appended to the end of data before sending over serial port; default carriage return + newline",
            )
            parser.add_argument(
                "concatenate",
                default=" ",
                help="What the strings in data should be concatenated by if list; by default a space",
            )
            parser.add_argument(
                "read_until",
                default=None,
                help="What character the string should read until",
            )
            parser.add_argument(
                "strip",
                type=bool,
                default=False,
                help="If the string should be stripped of whitespaces and newlines before responding",
            )

            def post(self) -> dict:
                args = self.parser.parse_args(strict=True)

                if _self._verbose:
                    print("Arguments for /send/get_first:", args)

                res = self.conn.get_first_response(
                    *args["data"],
                    is_bytes=False,
                    ending=args["ending"],
                    concatenate=args["concatenate"],
                    read_until=args["read_until"],
                    strip=args["strip"]
                )

                if res is None:
                    flask_restful.abort(502, message="Nothing received")

                return {"message": "OK", "data": res}

        return _GetFirst

    def _wait_for_response(_self) -> t.Type[ConnectionResource]:
        """/get/wait"""

        class _WaitResponse(ConnectionResource):

            parser = reqparse.RequestParser()

            parser.add_argument(
                "response",
                required=True,
                help="Which response the program should wait for; is required",
            )
            parser.add_argument(
                "read_until",
                default=None,
                help="What character the string should read until",
            )
            parser.add_argument(
                "strip",
                type=bool,
                default=False,
                help="If the string should be stripped of whitespaces and newlines before responding",
            )

            def post(self) -> dict:
                args = self.parser.parse_args(strict=True)

                if _self._verbose:
                    print("Arguments for /get/wait:", args)

                res = self.conn.wait_for_response(
                    response=args["response"],
                    read_until=args["read_until"],
                    strip=args["strip"],
                )

                if not res:
                    flask_restful.abort(502, message="Nothing received")

                return {"message": "OK"}

        return _WaitResponse

    def _send_for_response(_self) -> t.Type[ConnectionResource]:
        """/send/get"""

        class _SendResponse(ConnectionResource):

            parser = reqparse.RequestParser()

            parser.add_argument(
                "response",
                required=True,
                help="Which response the program should wait for; is required",
            )
            parser.add_argument(
                "data",
                required=True,
                action="append",
                help="Data the serial port should send; is required",
            )
            parser.add_argument(
                "ending",
                default="\r\n",
                help="Ending that will be appended to the end of data before sending over serial port; default carriage return + newline",
            )
            parser.add_argument(
                "concatenate",
                default=" ",
                help="What the strings in data should be concatenated by if list; by default a space",
            )
            parser.add_argument(
                "read_until",
                default=None,
                help="What character the string should read until",
            )
            parser.add_argument(
                "strip",
                type=bool,
                default=False,
                help="If the string should be stripped of whitespaces and newlines before responding",
            )

            def post(self) -> dict:
                args = self.parser.parse_args(strict=True)

                if _self._verbose:
                    print("Arguments for /send/get:", args)

                res = self.conn.send_for_response(
                    args["response"],
                    *args["data"],
                    ending=args["ending"],
                    concatenate=args["concatenate"],
                    read_until=args["read_until"],
                    strip=args["strip"]
                )

                if not res:
                    flask_restful.abort(502, message="Nothing received")

                return {"message": "OK"}

        return _SendResponse

    def _connection_state(_self) -> t.Type[Connection]:
        """/connection_state"""

        class _ConnectionState(ConnectionResource):
            def get(self) -> dict:
                return {
                    "message": "OK",
                    "state": {
                        "timeout": self.conn.timeout,
                        "send_interval": self.conn.send_interval,
                        "available": self.conn.available,
                        "port": self.conn.port,
                    },
                }

        return _ConnectionState

    def _connected(_self) -> t.Type[Connection]:
        """/connected"""

        class _GetConnectedState(ConnectionResource):
            def get(self) -> dict:
                return {"message": "OK", "connected": self.conn.connected}

        return _GetConnectedState

    # both throwaway as connection not needed
    def _list_all(_self) -> t.Type[ConnectionResource]:
        """/list_ports"""

        class _ListAll(ConnectionResource):
            def get(self) -> dict:
                res = all_ports()

                return {
                    "message": "OK",
                    "ports": [[port, desc, tech] for port, desc, tech in res],
                }

        return _ListAll
