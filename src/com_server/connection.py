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
    it makes other methods that may also be useful to the user
    when communicating with the classes.
    
    Some of the methods include:
    - `receive_str()`: Receives as a string rather than bytes object
    - `get_first_response()`: Gets the first response from the Serial port after sending something (breaks when timeout reached)
    - `send_for_response()`: Continues sending something until the connection receives a given response (breaks when timeout reached)
    - `wait_for_response()`: Waits until the connection receives a given response (breaks when timeout reached)

    Other methods can generally help the user with interacting with the classes:
    - `all_ports()`: Lists all available COM ports.
    - `run_func()`: A method that takes in a `main` function and calls it repeatedly with a delay.
    """

    def conv_bytes_to_str(self, rcv: bytes, read_until: t.Union[str, None] = None, strip: bool = True) -> t.Union[str, None]:
        """Convert bytes receive object to a string.

        Parameters:
        - `rcv` (bytes): A bytes object. If None, then the function will return None.
        - `read_until` (str, None) (optional): Will return a string that terminates with `read_until`, excluding `read_until`. 
        For example, if the string was `"abcdefg123456\\n"`, and `read_until` was `\\n`, then it will return `"abcdefg123456"`.
        If there are multiple occurrences of `read_until`, then it will return the string that terminates with the first one.
        If `read_until` is None or it doesn't exist, the it will return the entire string. By default None.
        - `strip` (bool) (optional): If True, then strips spaces and newlines from either side of the processed string before returning.
        If False, returns the processed string in its entirety. By default True.

        Returns:
        - A `str` representing the data
        - None if `rcv` is None
        """

        if (rcv is None):
            return None

        res = rcv.decode("utf-8")

        try:
            ret = res[0:res.index(str(read_until))] # sliced string
            if (strip):
                return ret.strip()
            else:
                return ret

        except (ValueError, TypeError):
            # read_until does not exist or it is None, so return the entire thing
            if (strip):
                return res.strip()
            else: 
                return res

    def receive_str(self, read_until: t.Union[str, None] = None, num_before: int = 0, strip: bool = True) -> "t.Union[None, tuple[str]]":
        """Returns the most recent receive object as a string.

        The receive thread will continuously detect receive data and put the `bytes` objects in the `rcv_queue`. 
        If there are no parameters, the method will return the most recent received data.
        If `num_before` is greater than 0, then will return `num_before`th previous data.
            - Note: Must be less than the current size of the queue and greater or equal to 0 
                - If not, returns None (no data)
            - Example:
                - 0 will return the most recent received data
                - 1 will return the 2nd most recent received data
                - ...
        
        Note that the data will be read as ALL the data available in the Serial port,
        or `Serial.read_all()`.

        This method will take in the input from `receive()` and put it in 
        `conv_bytes_to_str()`, then return it.

        Parameters:
        - `read_until` (str, None) (optional): Will return a string that terminates with `read_until`, excluding `read_until`. 
        For example, if the string was `"abcdefg123456\\n"`, and `read_until` was `\\n`, then it will return `"abcdefg123456"`.
        If `read_until` is None, the it will return the entire string. By default None.
        - `num_before` (int) (optional): Which receive object to return. By default 0.
        - `strip` (bool) (optional): If True, then strips the received and processed string of whitespace and newlines, then 
        returns the result. If False, then returns the raw result. By default True.

        Returns:
        - A `tuple` representing the `(timestamp received, string data)`
        - `None` if no data was found or port not open
        """
        
        rcv_tuple = self.receive(num_before=num_before)
        if (rcv_tuple is None):
            # return if None
            return None

        str_data = self.conv_bytes_to_str(rcv_tuple[1], read_until=read_until, strip=strip)

        return (rcv_tuple[0], str_data)
    
    def get_first_response(self, is_bytes: bool = True, *args: "tuple[t.Any]", check_type: bool = True, ending: str = "\r\n", concatenate: str = ' ', read_until: t.Union[str, None]) -> t.Union[bytes, str, None]:
        """Gets the first response from the Serial port after sending something.

        This method works almost the same as `send()` (see `self.send()`). 
        It also returns a string representing the first response from the Serial port after sending.
        All `*args` and `check_type`, `ending`, and `concatenate`, will be sent to `send()`.

        If there is no response after reaching the timeout, then it breaks out of the method.

        Parameters:
        - `is_bytes`: If False, then passes to `conv_bytes_to_str()` and returns a string
        with given options `read_until` and `strip`. See `conv_bytes_to_str()` for more details.
        If True, then returns raw `bytes` data. By default True.
        - See `send()`

        Returns:
        - A string or bytes representing the first response from the Serial port.
        - None if there was no data or timeout reached.
        """
    
    def send_for_response(self, response: t.Union[str, bytes], *args: "tuple[t.Any]", strip: bool = True, check_type: bool = True, ending: str = "\r\n", concatenate: str = ' ') -> bool:
        """Continues sending something until the connection receives a given response.

        This method will call `send()` and `receive()` repeatedly (calls again if does not match given `response` parameter).
        See `send()` for more details on `*args` and `check_type`, `ending`, and `concatenate`, as these will be passed to the method.
        Will return `true` on success and `false` on failure (reached timeout)

        Parameters:
        - `response` (str, bytes): The receive data that the program looks for after sending.
        If given a string, then compares the string to the response after it is decoded in `utf-8`.
        If given a bytes, then directly compares the bytes object to the response.
        - `strip` (bool) (optional). If True, then strips receive of spaces and newlines 
        at the end before comparing to parameter `response`. Applies for both `str` and `bytes`. 
        If False, then compares the raw data to parameter `response`. 
        - All other parameters will be passed to `send()`. For other parameters, see `send()` 

        Returns:
        - `true` on success: The incoming received data matched `response`.
        - `false` on failure: Incoming data did not match `response`, or `timeout` was reached.
        """

    def wait_for_response(self, response: t.Union[str, bytes]) -> bool:
        """Waits until the connection receives a given response.

        This method will call `receive()` repeatedly until it
        returns a string that matches `response`

        Parameters:
        - `response` (str) (bytes): The receive data that the program is loking for.
        If given a string, then compares the string to the response after it is decoded in `utf-8`.
        If given a bytes, then directly compares the bytes object to the response.
        """
    
    def all_ports(self) -> t.Generator:
        """Lists all available Serial ports.
        
        Calls `tools.all_ports()`, which itself calls `serial.tools.list_ports.comports()`.
        For more information, see [here](https://pyserial.readthedocs.io/en/latest/tools.html#module-serial.tools.list_ports).

        Parameters: none

        Returns: A generator-like object (see link above)
        """
    
