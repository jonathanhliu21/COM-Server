#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""

"""

import time
import typing as t

from . import base_connection

class Connection(base_connection.BaseConnection):
    """A more user-friendly interface with the Serial port.

    In addition to the four basic methods (see `BaseConnection`),
    it makes other methods that may also be useful to the user.
    
    Some of the methods include:
    - `get_first_response()`: Gets the first response from the Serial port after sending something (breaks when timeout reached)
    - `send_for_response()`: Continues sending something until the connection receives a given response (breaks when timeout reached)
    - `wait_for_response()`: Waits until the connection receives a given response (breaks when timeout reached)
    - `send_after_response()`: Only send something after the connection receives a given response (breaks when timeout reached)
    """

    def get_first_response(self, *args: "tuple[t.Any]", **kwargs) -> str:
        """Gets the first response from the Serial port after sending something.

        This method works almost the same as `send()` (see `self.send()`). 
        It also returns a string representing the first response from the Serial port after sending.
        All `*args` and `**kwargs` will be sent to `send()`.

        If there is no response after reaching the timeout, then it breaks out of the function.

        Parameters:
        - See `send()`

        Returns:
        - A string representing the first response from the Serial port.
        """
    
    def send_for_response(self, response: str, *args: "tuple[t.Any]", strip: bool = True, **kwargs) -> bool:
        """Continues sending something until the connection receives a given response

        This method will call `send()` and `receive()` repeatedly (calls again if does not match given `response` parameter).
        See `send()` for more details on `*args` and `**kwargs`
        Will return `true` on success and `false` on failure (reached timeout)

        Parameters:
        - `response` (str): The receive data that the program looks for after sending.
        - `strip` (bool) (optional). If True, then strips receive of spaces and newlines 
        at the end before comparing to parameter `response`.
        If False, then compares the raw data to parameter `response`. 
        - For other parameters, see `send()` 

        Returns:
        - `true` on success: The incoming received data matched `response`.
        - `false` on failure: Incoming data did not match `response`.

        """
