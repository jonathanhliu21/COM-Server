# /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Contains class with builtin functions that match `Connection` object

Endpoints include:
    - `/send` (POST): Send something through the serial port using `Connection.send()` with parameters in request; equivalent to `Connection.send(...)`
    - `/receive` (GET, POST): Respond with the most recent received string from the serial port; equivalent to `Connection.receive_str(...)`
    - `/receive/all` (GET, POST): Returns the entire receive queue; equivalent to `Connection.get_all_rcv_str(...)`
    - `/get` (GET, POST): Respond with the first string from serial port after request; equivalent to `Connection.get(str, ...)`
    - `/send/get_first` (POST): Responds with the first string response from the serial port after sending data, with data and parameters in request; equivalent to `Connection.get_first_response(is_bytes=False, ...)`
    - `/get/wait` (POST): Waits until connection receives string data given in request; different response for success and failure; equivalent to `Connection.wait_for_response(...)`
    - `/send/get` (POST): Continues sending something until connection receives data given in request; different response for success and failure; equivalent to `Connection.send_for_response(...)`
    - `/connected` (GET): Indicates if the serial port is currently connected or not
    - `/list_ports` (GET): Lists all available Serial ports

The above endpoints will not be available if the class is used.
"""

import typing as t

import flask_restful
from flask_restful import reqparse

from . import Connection, ConnectionResource, RestApiHandler, all_ports


class Builtins:
    """Contains implementations of endpoints that call methods of `Connection` object
    
    Endpoints include:
        - `/send` (POST): Send something through the serial port using `Connection.send()` with parameters in request; equivalent to `Connection.send(...)`
        - `/receive` (GET, POST): Respond with the most recent received string from the serial port; equivalent to `Connection.receive_str(...)`
        - `/receive/all` (GET, POST): Returns the entire receive queue; equivalent to `Connection.get_all_rcv_str(...)`
        - `/get` (GET, POST): Respond with the first string from serial port after request; equivalent to `Connection.get(str, ...)`
        - `/send/get_first` (POST): Responds with the first string response from the serial port after sending data, with data and parameters in request; equivalent to `Connection.get_first_response(is_bytes=False, ...)`
        - `/get/wait` (POST): Waits until connection receives string data given in request; different response for success and failure; equivalent to `Connection.wait_for_response(...)`
        - `/send/get` (POST): Continues sending something until connection receives data given in request; different response for success and failure; equivalent to `Connection.send_for_response(...)`
        - `/connected` (GET): Indicates if the serial port is currently connected or not
        - `/list_ports` (GET): Lists all available Serial ports

    The above endpoints will not be available if the class is used.
    """

    def __init__(self, handler: RestApiHandler, verbose: bool = False) -> None:
        """Constructor for class that contains builtin endpoints

        Adds endpoints to given `RestApiHandler` class;
        uses `Connection` object within the class to handle
        serial data.

        Example usage:
        ```
        conn = com_server.Connection(...)
        handler = com_server.RestApiHandler(conn)
        builtins = com_server.Builtins(handler)

        handler.run() # runs the server
        ```

        Parameters:
        - `api`: The `RestApiHandler` class that this class should wrap around
        - `verbose`: Prints the arguments it receives to stdout. Should not be used in production.
        """

        if (not isinstance(handler._conn, Connection)):
            raise TypeError("The connection object passed into the handler must be a Connection type")

        self._handler = handler
        self._verbose = verbose

        # add all endpoints
        self._add_all()
    
    def _add_all(self):
        """Adds all endpoints to handler"""
        
        # /send 
        self._handler.add_endpoint("/send")(self._send)
        
        # /receive
        self._handler.add_endpoint("/receive")(self._receive)

        # /receive/all
        self._handler.add_endpoint("/receive/all")(self._receive_all)

        # /get
        self._handler.add_endpoint("/get")(self._get)

        # /send/get_first
        self._handler.add_endpoint("/send/get_first")(self._get_first_response)

        # /get/wait
        self._handler.add_endpoint("/get/wait")(self._wait_for_response)

        # /send/get
        self._handler.add_endpoint("/send/get")(self._send_for_response)

        # /connected
        self._handler.add_endpoint("/connected")(self._connected)

        # /list_ports
        self._handler.add_endpoint("/list_ports")(self._list_all)
    
    # throwaway variable at beginning because it is part of class, "self" would be passed
    def _send(_, conn: Connection) -> t.Type[ConnectionResource]:
        """
        Endpoint to send data to the serial port.
        Calls `Connection.send()` with given arguments in request.

        Method: POST

        Arguments:
        - "data" (str, list): The data to send; can be provided in multiple arguments, which will be concatenated with the `concatenate` variable.
        - "ending" (str) (optional): A character or string that will be appended to `data` after being concatenated before sending to the serial port.
        By default a carraige return + newline.
        - "concatenate" (str) (optional): The character or string that elements of "data" should be concatenated by if its size is greater than 1;
        won't affect "data" if the size of the list is equal to 1. By default a space.

        Responses:
        - `200 OK`: 
            - `{"message": "OK"}` if send through
        - `502 Bad Gateway`: 
            - `{"message": "Failed to send"}` if something went wrong with sending (i.e. `Connection.send()` returned false)
        """

        class _Sending(ConnectionResource):
            # make parser once when class is declared, don't add arguments each time request is made aka don't put in post()
            parser = reqparse.RequestParser()
            parser.add_argument("data", required=True, action='append', help="Data the serial port should send; is required")
            parser.add_argument("ending", default="\r\n", help="Ending that will be appended to the end of data before sending over serial port; default carriage return + newline")
            parser.add_argument("concatenate", default=' ', help="What the strings in data should be concatenated by if list; by default a space")

            def post(self) -> dict:
                args = self.parser.parse_args(strict=True)

                # no need for check_type because everything will be parsed as a string
                res = conn.send(*args["data"], ending=args["ending"], concatenate=args["concatenate"])

                if (not res):
                    # abort if failed to send
                    flask_restful.abort(502, message="Failed to send")
                
                return {"message": "OK"}

        return _Sending
    
    def _receive(_, conn: Connection) -> t.Type[ConnectionResource]:
        """
        Endpoint to get data that was recently received.
        If POST, calls `Connection.receive_str(...)` with arguments given in request.
        If GET, calls `Connection.receive_str(...)` with default arguments (except strip=True). This means
        that it responds with the latest received string with everything included after 
        being stripped of whitespaces and newlines.

        Method: GET, POST

        Arguments (POST only):
        - "num_before" (int) (optional): How recent the receive object should be.
        If 0, then returns most recent received object. If 1, then returns
        the second most recent received object, etc. By default 0.
        - "read_until" (str, null) (optional): Will return a string that terminates with
        character in "read_until", excluding that character or string. For example,
        if the bytes was `b'123456'` and "read_until" was 6, then it will return
        `'12345'`. If ommitted, then returns the entire string. By default returns entire string.
        - "strip" (bool) (optional): If true, then strips received and processed string of
        whitespaces and newlines and responds with result. Otherwise, returns raw string. 
        Note that using {"strip": False} may not work; it is better to omit it.
        By default False.

        Response:
        - `200 OK`:
            - `{"message": "OK", "timestamp": ..., "data": "..."}` where "timestamp"
            is the Unix epoch time that the message was received and "data" is the
            data that was processed. If nothing was received, then "data" and "timestamp"
            would be None/null.
        """

        class _Receiving(ConnectionResource):

            parser = reqparse.RequestParser()
            parser.add_argument("num_before", type=int, default=0, help="Which receive data to return")
            parser.add_argument("read_until", default=None, help="What character the string should read until")
            parser.add_argument("strip", type=bool, default=False, help="If the string should be stripped of whitespaces and newlines before responding")

            def get(self) -> dict:
                res = conn.receive_str()

                return {
                    "message": "OK",
                    "timestamp": res[0] if isinstance(res, tuple) else None,
                    "data": res[1] if isinstance(res, tuple) else None
                }

            def post(self) -> dict:
                args = self.parser.parse_args(strict=True)

                res = conn.receive_str(num_before=args["num_before"], read_until=args["read_until"], strip=args["strip"])

                return {
                    "message": "OK",
                    "timestamp": res[0] if isinstance(res, tuple) else None,
                    "data": res[1] if isinstance(res, tuple) else None
                }
        
        return _Receiving
    
    def _receive_all(_, conn: Connection) -> t.Type[ConnectionResource]:
        """
        Returns the entire receive queue. Calls `Connection.get_all_rcv_str(...)`.
        If POST then uses arguments in request.
        If GET then uses default arguments (except strip=True), which means that
        that it responds with the latest received string with everything included after 
        being stripped of whitespaces and newlines.

        Method: GET, POST

        Arguments (POST only):
        - "read_until" (str, null) (optional): Will return a string that terminates with
        character in "read_until", excluding that character or string. For example,
        if the bytes was `b'123456'` and "read_until" was 6, then it will return
        `'12345'`. If ommitted, then returns the entire string. By default returns entire string.
        - "strip" (bool) (optional): If true, then strips received and processed string of
        whitespaces and newlines and responds with result. Otherwise, returns raw string. 
        Note that using {"strip": False} may not work; it is better to omit it.
        By default False.

        Response:
        - `200 OK`:
            - `{"message": "OK", "timestamps": [...], "data": [...]}`: where "timestamps" 
            contains the list of timestamps in the receive queue and "data" contains the 
            list of data in the receive queue. The indices for "timestamps" and "data" match.
        """ 

        class _ReceiveAll(ConnectionResource):
            
            parser = reqparse.RequestParser()
            parser.add_argument("read_until", default=None, help="What character the string should read until")
            parser.add_argument("strip", type=bool, default=False, help="If the string should be stripped of whitespaces and newlines before responding")

            def get(self) -> dict:
                all_rcv = conn.get_all_rcv_str()

                return {
                    "message": "OK",
                    "timestamps": [ts for ts, _ in all_rcv],
                    "data": [data for _, data in all_rcv]
                }

            def post(self) -> dict:
                args = self.parser.parse_args(strict=True)

                all_rcv = conn.get_all_rcv_str(read_until=args["read_until"], strip=args["strip"])

                return {
                    "message": "OK",
                    "timestamps": [ts for ts, _ in all_rcv],
                    "data": [data for _, data in all_rcv]
                }

        return _ReceiveAll
    
    def _get(_, conn: Connection) -> t.Type[ConnectionResource]:
        """
        Waits for the first string from the serial port after request.
        If no string after timeout (specified on server side), then responds with 502.
        Calls `Connection.get(str, ...)`.
        If POST then uses arguments in request. 
        If GET then uses default arguments (except strip=True), which means that
        that it responds with the latest received string with everything included after 
        being stripped of whitespaces and newlines.

        Method: GET, POST

        Arguments (POST only):
        - "read_until" (str, null) (optional): Will return a string that terminates with
        character in "read_until", excluding that character or string. For example,
        if the bytes was `b'123456'` and "read_until" was 6, then it will return
        `'12345'`. If ommitted, then returns the entire string. By default returns entire string.
        - "strip" (bool) (optional): If true, then strips received and processed string of
        whitespaces and newlines and responds with result. Otherwise, returns raw string. 
        Note that using {"strip": False} may not work; it is better to omit it.
        By default False.

        Response:
        - `200 OK`:
            - `{"message": "OK", "data": "..."}` where "data" is received data
        - `502 Bad Gateway`: 
            - `{"message": "Nothing received"}` if nothing was received from the serial port
            within the timeout specified on the server side.   
        """

        class _Get(ConnectionResource):
        
            parser = reqparse.RequestParser()
            parser.add_argument("read_until", default=None, help="What character the string should read until")
            parser.add_argument("strip", type=bool, default=False, help="If the string should be stripped of whitespaces and newlines before responding")

            def get(self) -> dict:
                got = conn.get(str)

                if (got is None):
                    flask_restful.abort(502, message="Nothing received")

                return {
                    "message": "OK",
                    "data": got
                }

            def post(self) -> dict:
                args = self.parser.parse_args(strict=True)

                got = conn.get(str, read_until=args["read_until"], strip=args["strip"])

                if (got is None):
                    flask_restful.abort(502, message="Nothing received")

                return {
                    "message": "OK",
                    "data": got
                }

        return _Get

    def _get_first_response(_, conn: Connection) -> t.Type[ConnectionResource]:
        """
        Respond with the first string received from the 
        serial port after sending something given in request.
        Calls `Connection.get_first_response(is_bytes=False, ...)`.

        Method: POST

        Arguments:
        - "data" (str, list): Everything that is to be sent, each as a separate parameter. Must have at least one parameter.
        - "ending" (str) (optional): The ending of the bytes object to be sent through the Serial port. By default a carraige return ("\\r\\n")
        - "concatenate" (str) (optional): What the strings in args should be concatenated by
        - "read_until" (str, None) (optional): Will return a string that terminates with `read_until`, excluding `read_until`. 
        For example, if the string was `"abcdefg123456\\n"`, and `read_until` was `\\n`, then it will return `"abcdefg123456"`.
        If `read_until` is None, the it will return the entire string. By default None.
        - "strip" (bool) (optional): If true, then strips received and processed string of
        whitespaces and newlines and responds with result. Otherwise, returns raw string. 
        Note that using {"strip": False} may not work; it is better to omit it.
        By default False.

        Response:
        - `200 OK`:
            - `{"message": "OK", "data": "..."}` where "data" is the
            data that was processed. 
        - `502 Bad Gateway`: 
            - `{"message": "Nothing received"}` if nothing was received from the serial port
            within the timeout specified on the server side.   
        """ 

        class _GetFirst(ConnectionResource):

            parser = reqparse.RequestParser()
            
            parser.add_argument("data", required=True, action='append', help="Data the serial port should send; is required")
            parser.add_argument("ending", default="\r\n", help="Ending that will be appended to the end of data before sending over serial port; default carriage return + newline")
            parser.add_argument("concatenate", default=' ', help="What the strings in data should be concatenated by if list; by default a space")
            parser.add_argument("read_until", default=None, help="What character the string should read until")
            parser.add_argument("strip", type=bool, default=False, help="If the string should be stripped of whitespaces and newlines before responding")

            def post(self) -> dict:
                args = self.parser.parse_args(strict=True)

                res = conn.get_first_response(*args["data"], is_bytes=False, ending=args["ending"], concatenate=args["concatenate"], read_until=args["read_until"], strip=args["strip"])

                if (res is None):
                    flask_restful.abort(502, message="Nothing received")
                
                return {
                    "message": "OK",
                    "data": res
                }

        return _GetFirst
    
    def _wait_for_response(_, conn: Connection) -> t.Type[ConnectionResource]:
        """
        Waits until connection receives string data given in request.
        Calls `Connection.wait_for_response(...)`.

        Method: POST

        Arguments:
        - "response" (str): The string the program is waiting to receive.
        Compares to response to `Connection.receive_str()`.
        - "read_until" (str, None) (optional): Will return a string that terminates with `read_until`, excluding `read_until`. 
        For example, if the string was `"abcdefg123456\\n"`, and `read_until` was `\\n`, then it will return `"abcdefg123456"`.
        If `read_until` is None, the it will return the entire string. By default None.
        - "strip" (bool) (optional): If true, then strips received and processed string of
        whitespaces and newlines and responds with result. Otherwise, returns raw string. 
        Note that using {"strip": False} may not work; it is better to omit it.
        By default False.

        Response:
        - `200 OK`:
            - `{"message": "OK"}` if everything was able to send through
        - `502 Bad Gateway`: 
            - `{"message": "Nothing received"}` if nothing was received from the serial port
            within the timeout specified on the server side.   
        """

        class _WaitResponse(ConnectionResource):

            parser = reqparse.RequestParser()
            
            parser.add_argument("response", required=True, help="Which response the program should wait for; is required")
            parser.add_argument("read_until", default=None, help="What character the string should read until")
            parser.add_argument("strip", type=bool, default=False, help="If the string should be stripped of whitespaces and newlines before responding")

            def post(self) -> dict:
                args = self.parser.parse_args(strict=True)
                
                res = conn.wait_for_response(response=args["response"], read_until=args["read_until"], strip=args["strip"])

                if (not res):
                    flask_restful.abort(502, message="Nothing received")
                
                return {"message": "OK"}
        
        return _WaitResponse
    
    def _send_for_response(_, conn: Connection) -> t.Type[ConnectionResource]:
        """
        Continues sending something until connection receives data given in request.
        Calls `Connection.send_for_response(...)`

        Method: POST

        Arguments:
        - "response" (str): The string the program is waiting to receive.
        Compares to response to `Connection.receive_str()`.
        - "data" (str, list): Everything that is to be sent, each as a separate parameter. Must have at least one parameter.
        - "ending" (str) (optional): The ending of the bytes object to be sent through the Serial port. By default a carraige return ("\\r\\n")
        - "concatenate" (str) (optional): What the strings in args should be concatenated by
        - "read_until" (str, None) (optional): Will return a string that terminates with `read_until`, excluding `read_until`. 
        For example, if the string was `"abcdefg123456\\n"`, and `read_until` was `\\n`, then it will return `"abcdefg123456"`.
        If `read_until` is None, the it will return the entire string. By default None.
        - "strip" (bool) (optional): If true, then strips received and processed string of
        whitespaces and newlines and responds with result. Otherwise, returns raw string. 
        Note that using {"strip": False} may not work; it is better to omit it.
        By default False.

        Response:
        - `200 OK`:
            - `{"message": "OK"}` if everything was able to send through
        - `502 Bad Gateway`: 
            - `{"message": "Nothing received"}` if nothing was received from the serial port
            within the timeout specified on the server side.   
        """

        class _SendResponse(ConnectionResource):

            parser = reqparse.RequestParser()
            
            parser.add_argument("response", required=True, help="Which response the program should wait for; is required")
            parser.add_argument("data", required=True, action='append', help="Data the serial port should send; is required")
            parser.add_argument("ending", default="\r\n", help="Ending that will be appended to the end of data before sending over serial port; default carriage return + newline")
            parser.add_argument("concatenate", default=' ', help="What the strings in data should be concatenated by if list; by default a space")
            parser.add_argument("read_until", default=None, help="What character the string should read until")
            parser.add_argument("strip", type=bool, default=False, help="If the string should be stripped of whitespaces and newlines before responding")

            def post(self) -> dict:
                args = self.parser.parse_args(strict=True)

                res = conn.send_for_response(args["response"], *args["data"], ending=args["ending"], concatenate=args["concatenate"], read_until=args["read_until"], strip=args["strip"])

                if (not res):
                    flask_restful.abort(502, message="Nothing received")

                return {"message": "OK"}

        return _SendResponse
    
    def _connected(self, conn: Connection) -> t.Type[Connection]:
        """
        Indicates if the serial port is currently connected or not.
        Returns the `Connection.connected` property. 

        Method: GET

        Arguments:
            None
        
        Response:
        - `200 OK`:
            - `{"message": "OK", "connected": ...}`: where connected is the connected state: `true` if connected, `false` if not.
        """

        class _GetConnectedState(ConnectionResource):
            def get(self) -> dict:
                return {
                    "message": "OK",
                    "connected": conn.connected
                }
        
        return _GetConnectedState
    
    # both throwaway as connection not needed
    def _list_all(_, __) -> t.Type[ConnectionResource]:
        """
        Lists all available Serial ports. Calls `com_server.tools.all_ports()`
        and returns list of lists of size 3: [`port`, `description`, `technical description`]

        Method: GET

        Arguments:
            None
        
        Response:
        - `200 OK`:
            - `{"message": "OK", ports = [["...", "...", "..."], "..."]}` where "ports"
            is a list of lists of size 3, each one indicating the port, description, and
            technical description
        """

        class _ListAll(ConnectionResource):
            def get(self) -> dict:
                res = all_ports()

                return {
                    "message": "OK",
                    "ports": [[port, desc, tech] for port, desc, tech in res]
                }
            
        return _ListAll

