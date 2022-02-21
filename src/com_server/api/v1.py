# /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Version 1 of Builtin API. All endpoints below will be prefixed with /v1/ and cannot be used.
"""

import typing as t

from flask_restful import reqparse, abort

from .. import ConnectionResource, ConnectionRoutes, all_ports


class V1:
    """
    Builtin routes for version 1 API.

    These routes will actually somewhat follow RESTful rules, unlike
    the version 0 API. This version also allows custom prefixing.
    """

    def __init__(self, handler: ConnectionRoutes, prefix: str = "v1") -> None:
        """Wrapper for handler that adds builtin routes

        Parameters:

        - `handler`: The ConnectionRoutes object to add builtin routes to
        - `prefix`: The prefix of the routes (`http://hostname/{prefix}/...`). By default "v1".
        """

        self._handler = handler
        self._prefix = prefix

        _endpoint_map = {
            "/send": self._Sender,
            "/receive/<int:num_before>": self._Receiver,
            "/receive": self._All_Received,
            "/get": self._Get,
            "/first_response": self._Get_First,
            "/connection_state": self._Connection_State,
            "/all_ports": self._All_Ports,
        }

        for endpoint in _endpoint_map:
            self._handler.add_resource(f"/{prefix}{endpoint}")(_endpoint_map[endpoint])

    class _Sender(ConnectionResource):
        """/send"""

        parser = reqparse.RequestParser()
        parser.add_argument(
            "data",
            required=True,
            action="append",
            help="Data the serial port should send",
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

            # no need for check_type because everything will be parsed as a string
            res = self.conn.send(
                *args["data"],
                ending=args["ending"],
                concatenate=args["concatenate"],
            )

            if not res:
                # abort if failed to send
                return {"message": "Failed to send"}

            return {"message": "OK", "data": args}

    class _Receiver(ConnectionResource):
        """/receive/<int:num_before>"""

        def get(self, num_before: int) -> dict:
            res = self.conn.receive_str(num_before=num_before)

            if not isinstance(res, tuple):
                abort(404, message="Receive item not found")

            return {
                "message": "OK",
                "timestamp": res[0] if isinstance(res, tuple) else None,
                "data": res[1] if isinstance(res, tuple) else None,
            }

    class _All_Received(ConnectionResource):
        """/receive"""

        def get(self) -> dict:
            all_rcv = self.conn.get_all_rcv_str()

            return {
                "message": "OK",
                "timestamps": [ts for ts, _ in all_rcv],
                "data": [data for _, data in all_rcv],
            }

    class _Get(ConnectionResource):
        """/get"""

        def get(self) -> dict:
            got = self.conn.get(str)

            if got is None:
                return {"message": "Nothing received"}

            return {"message": "OK", "data": got}

    class _Get_First(ConnectionResource):
        """/first_response"""

        parser = reqparse.RequestParser()

        parser.add_argument(
            "data",
            required=True,
            action="append",
            help="Data the serial port should send",
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

            res = self.conn.get_first_response(
                *args["data"],
                is_bytes=False,
                ending=args["ending"],
                concatenate=args["concatenate"],
            )

            if res is None:
                return {"message": "Nothing received"}

            return {"message": "OK", "data": res}

    class _Connection_State(ConnectionResource):
        """/connection_state"""

        def get(self) -> dict:
            return {
                "message": "OK",
                "state": {
                    "connected": self.conn.connected,
                    "timeout": self.conn.timeout,
                    "send_interval": self.conn.send_interval,
                    "available": self.conn.available,
                    "port": self.conn.port,
                },
            }

    class _All_Ports(ConnectionResource):
        """/all_ports"""

        def get(self) -> dict:
            res = all_ports()

            return {
                "message": "OK",
                "ports": [[port, desc, tech] for port, desc, tech in res],
            }
