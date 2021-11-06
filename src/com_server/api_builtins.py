# /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Contains class with builtin functions that match `Connection` object

Endpoints include:
    - `/send` (POST): Send something through the serial port using `Connection.send()` with parameters in request; equivalent to `Connection.send()`
    - `/receive` (GET): Respond with the most recent received string from the serial port; equivalent to `Connection.receive_str()`
    - `/get` (GET): Respond with the first string from serial port after request; equivalent to `Connection.get(str)`
    - `/send/get_first` (POST): Responds with the first string response from the serial port after sending data, with data and parameters in request; equivalent to `Connection.get_first_response()`
    - `/get/wait` (POST): Waits until connection receives string data given in request; different response for success and failure; equivalent to `Connection.wait_for_response()`
    - `/send/get` (POST): Continues sending something until connection receives data given in request; different response for success and failure; equivalent to `Connection.send_for_response()`
    - `/list_ports` (GET): Lists all available Serial ports

The above endpoints will not be valid if the class is used
"""

import typing as t

from flask_restful import reqparse
import flask_restful

from . import RestApiHandler, ConnectionResource, Connection

class Builtins:
    """Contains implementations of endpoints that call methods of `Connection` object
    
    Endpoints include:
        - `/send` (POST): Send something through the serial port using `Connection.send()` with parameters in request; equivalent to `Connection.send()`
        - `/receive` (GET): Respond with the most recent received string from the serial port; equivalent to `Connection.receive_str()`
        - `/get` (GET): Respond with the first string from serial port after request; equivalent to `Connection.get(str)`
        - `/send/get_first` (POST): Responds with the first string response from the serial port after sending data, with data and parameters in request; equivalent to `Connection.get_first_response()`
        - `/get/wait` (POST): Waits until connection receives string data given in request; different response for success and failure; equivalent to `Connection.wait_for_response()`
        - `/send/get` (POST): Continues sending something until connection receives data given in request; different response for success and failure; equivalent to `Connection.send_for_response()`
        - `/list_ports` (GET): Lists all available Serial ports

    The above endpoints will not be valid if the class is used
    """

    def __init__(self, handler: RestApiHandler) -> None:
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
        """

        # TODO: add function to handle adding endpoints
        handler.add_endpoint("/send")(self.send)
    
    # throwaway variable at beginning because it is part of class, "self" would be passed
    def send(_, conn: Connection) -> t.Type[ConnectionResource]:
        """
        Endpoint to send data to the serial port.

        Method: POST

        Arguments:
        - "data": The data to send; can be provided in multiple arguments, which will be concatenated with the `concatenate` variable.
        - "ending": A character or string that will be appended to `data` after being concatenated before sending to the serial port.
        By default a carraige return + newline.
        - "concatenate": The character or string that elements of "data" should be concatenated by if its size is greater than 1;
        won't affect "data" if the size of the list is equal to 1.

        Responses:
        - `200 OK`: `{"message": "OK"}` if sent through
        - `502 Bad Gateway`: `{"message": "Failed to send"}` if something went wrong with sending (`Connection.send()` returned false)
        """

        class _Sending(ConnectionResource):
            # make parser once when class is declared, don't add arguments each time request is made aka don't put in post()
            parser = reqparse.RequestParser()
            parser.add_argument("data", required=True, action='append', help="Data the serial port should send; is required")
            parser.add_argument("ending", default="\r\n", help="Ending that will be appended to the end of data before sending over serial port; default carriage return + newline")
            parser.add_argument("concatenate", default=' ', help="what the strings in data should be concatenated by if list; by default a space")

            def post(self):
                args = self.parser.parse_args(strict=True)

                # no need for check_type because everything will be parsed as a string
                res = conn.send(*args["data"], ending=args["ending"], concatenate=args["concatenate"])

                if (not res):
                    # abort if failed to send
                    flask_restful.abort(502, message="Failed to send")
                
                return {"message": "OK"}

        return _Sending
