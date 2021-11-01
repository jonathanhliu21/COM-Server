#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""

"""

import time
import typing as t

from . import base_connection
from . import tools

class Connection(base_connection.BaseConnection):
    """A more user-friendly interface with the Serial port.

    In addition to the four basic methods (see `BaseConnection`),
    it makes other methods that may also be useful to the user
    when communicating with the classes.
    
    Some of the methods include:
    - `get()`: Gets first response after the time that the method was called.
    - `receive_str()`: Receives as a string rather than bytes object
    - `get_first_response()`: Gets the first response from the Serial port after sending something (breaks when timeout reached)
    - `send_for_response()`: Continues sending something until the connection receives a given response (breaks when timeout reached)
    - `wait_for_response()`: Waits until the connection receives a given response (breaks when timeout reached)

    Other methods can generally help the user with interacting with the classes:
    - `all_ports()`: Lists all available COM ports.
    - `run_func()`: A method that takes in a `main` method and calls it repeatedly with a delay.
    """

    def conv_bytes_to_str(self, rcv: bytes, read_until: t.Union[str, None] = None, strip: bool = True) -> t.Union[str, None]:
        """Convert bytes receive object to a string.

        Parameters:
        - `rcv` (bytes): A bytes object. If None, then the method will return None.
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
    
    def get(self, given_type: t.Type, read_until: t.Union[str, None] = None, strip: bool = True) -> t.Union[None, bytes, str]:
        """Gets first response after this method is called.

        This method differs from `receive()` because `receive()` returns
        the last element of the receive buffer, which could contain objects
        that were received before this function was called. This function
        waits for something to be received after it is called until it either
        gets the object or until the timeout is reached.

        Parameters:
        - `given_type` (type): either `bytes` or `str`, indicating which one to return. 
        Will raise exception if type is invalid, REGARDLESS of `self.exception`.
        - `read_until` (str, None) (optional): Will return a string that terminates with `read_until`, excluding `read_until`. 
        For example, if the string was `"abcdefg123456\\n"`, and `read_until` was `\\n`, then it will return `"abcdefg123456"`.
        If there are multiple occurrences of `read_until`, then it will return the string that terminates with the first one.
        If `read_until` is None or it doesn't exist, the it will return the entire string. By default None.
        - `strip` (bool) (optional): If True, then strips spaces and newlines from either side of the processed string before returning.
        If False, returns the processed string in its entirety. By default True.

        Returns:
        - None if no data received (timeout reached)
        - A `bytes` object indicating the data received if `type` is `bytes`
        """

        call_time = time.time() # time that the function was called

        if (given_type != str and given_type != bytes):
            raise TypeError("given_type must be str or bytes")
        
        if (given_type == str):
            return self._get_str(call_time, read_until=read_until, strip=strip)
        else:
            return self._get_bytes(call_time)

    def receive_str(self, num_before: int = 0, read_until: t.Union[str, None] = None, strip: bool = True) -> "t.Union[None, tuple[float, str]]":
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
        - `num_before` (int) (optional): Which receive object to return. By default 0.
        - `read_until` (str, None) (optional): Will return a string that terminates with `read_until`, excluding `read_until`. 
        For example, if the string was `"abcdefg123456\\n"`, and `read_until` was `\\n`, then it will return `"abcdefg123456"`.
        If `read_until` is None, the it will return the entire string. By default None.
        - `strip` (bool) (optional): If True, then strips the received and processed string of whitespace and newlines, then 
        returns the result. If False, then returns the raw result. By default True.

        Returns:
        - A `tuple` representing the `(timestamp received, string data)`
        - `None` if no connection (if self.exception == False), data was found, or port not open
        """

        # checks if connection is open.
        if (not self._check_connect()):
            return None
        
        rcv_tuple = self.receive(num_before=num_before)
        if (rcv_tuple is None):
            # return if None
            return None

        str_data = self.conv_bytes_to_str(rcv_tuple[1], read_until=read_until, strip=strip)

        return (rcv_tuple[0], str_data)
    
    def get_first_response(self, *args: "tuple[t.Any]", is_bytes: bool = True, check_type: bool = True, ending: str = "\r\n", concatenate: str = ' ', read_until: t.Union[str, None] = None, strip: bool = True) -> t.Union[bytes, str, None]:
        """Gets the first response from the Serial port after sending something.

        This method works almost the same as `send()` (see `self.send()`). 
        It also returns a string representing the first response from the Serial port after sending.
        All `*args` and `check_type`, `ending`, and `concatenate`, will be sent to `send()`.

        If there is no response after reaching the timeout, then it breaks out of the method.

        Parameters:
        - `*args`: Everything that is to be sent, each as a separate parameter. Must have at least one parameter.
        - `is_bytes`: If False, then passes to `conv_bytes_to_str()` and returns a string
        with given options `read_until` and `strip`. See `conv_bytes_to_str()` for more details.
        If True, then returns raw `bytes` data. By default True.
        - `check_type` (bool) (optional): If types in *args should be checked. By default True.
        - `ending` (str) (optional): The ending of the bytes object to be sent through the Serial port. By default a carraige return ("\\r\\n")
        - `concatenate` (str) (optional): What the strings in args should be concatenated by
        - `read_until` (str, None) (optional): Will return a string that terminates with `read_until`, excluding `read_until`. 
        For example, if the string was `"abcdefg123456\\n"`, and `read_until` was `\\n`, then it will return `"abcdefg123456"`.
        If `read_until` is None, the it will return the entire string. By default None.
        - `strip` (bool) (optional): If True, then strips the received and processed string of whitespace and newlines, then 
        returns the result. If False, then returns the raw result. By default True.

        Returns:
        - A string or bytes representing the first response from the Serial port.
        - None if there was no connection (if self.exception == False), no data, timeout reached, or send interval not reached.
        """

        if (not self._check_connect()):
            return None

        send_time = time.time() # tracks send time
        send_success = self.send(*args, check_type=check_type, ending=ending, concatenate=concatenate)

        # for receiving string or bytes
        rcv_func = self.receive if is_bytes else self.receive_str
        
        if (not send_success):
            return None

        r = None 
        if (is_bytes):
            r = rcv_func()
        else:
            # strings have read_until option
            r = rcv_func(read_until=read_until, strip=strip)

        st = time.time()

        # compares send time to receive time; return the first receive object where the send time < receive time
        while (r is None or r[0] < send_time):
            if (time.time() - st > self.timeout):
                # reached timeout

                return None
            
            if (is_bytes):
                r = rcv_func()
            else:
                # strings have read_until option
                r = rcv_func(read_until=read_until)

            time.sleep(0.05)
        
        return r[1]
    
    def wait_for_response(self, response: t.Union[str, bytes], after_timestamp: float = -1.0, read_until: t.Union[str, None] = None, strip: bool = True) -> bool:
        """Waits until the connection receives a given response.

        This method will call `receive()` repeatedly until it
        returns a string that matches `response` whose timestamp
        is greater than given timestamp (`after_timestamp`).

        Parameters:
        - `response` (str, bytes): The receive data that the program is loking for.
        If given a string, then compares the string to the response after it is decoded in `utf-8`.
        If given a bytes, then directly compares the bytes object to the response.
        If given anything else, converts to string.
        - `after_timestamp` (float): Look for responses that came after given time as the UNIX timestamp.
        By default the time that the method was called, or `time.time()`

        These parameters only apply if `response` is a string:
        - `read_until` (str, None) (optional): Will return a string that terminates with `read_until`, excluding `read_until`. 
        For example, if the string was `"abcdefg123456\\n"`, and `read_until` was `\\n`, then it will return `"abcdefg123456"`.
        If `read_until` is None, the it will return the entire string. By default None.
        - `strip` (bool) (optional): If True, then strips the received and processed string of whitespace and newlines, then 
        returns the result. If False, then returns the raw result. By default True.

        Returns:
        - True on success
        - False on failure: timeout reached because response has not been received.
        """

        after_timestamp = float(after_timestamp)
        if (after_timestamp < 0):
            # negative number to indicate program to use current time, time in parameter does not work
            after_timestamp = time.time()

        if (isinstance(response, str)):
            return self._wait_for_response_str(response, timestamp=after_timestamp, read_until=read_until, strip=strip)
        elif (isinstance(response, bytes)):
            return self._wait_for_response_bytes(response, timestamp=after_timestamp)
        else:
            return self._wait_for_response_str(str(response), timestamp=after_timestamp, read_until=read_until, strip=strip)

    def send_for_response(self, response: t.Union[str, bytes], *args: "tuple[t.any]", read_until: t.Union[str, None] = None, strip: bool = True, check_type: bool = True, ending: str = "\r\n", concatenate: str = ' ') -> bool:
        """continues sending something until the connection receives a given response.

        This method will call `send()` and `receive()` repeatedly (calls again if does not match given `response` parameter).
        See `send()` for more details on `*args` and `check_type`, `ending`, and `concatenate`, as these will be passed to the method.
        Will return `true` on success and `false` on failure (reached timeout)

        Parameters:
        - `response` (str, bytes): The receive data that the program looks for after sending.
        If given a string, then compares the string to the response after it is decoded in `utf-8`.
        If given a bytes, then directly compares the bytes object to the response.
        - `*args`: Everything that is to be sent, each as a separate parameter. Must have at least one parameter.
        - `check_type` (bool) (optional): If types in *args should be checked. By default True.
        - `ending` (str) (optional): The ending of the bytes object to be sent through the Serial port. By default a carraige return ("\\r\\n")
        - `concatenate` (str) (optional): What the strings in args should be concatenated by

        These parameters only apply if `response` is a string:
        - `read_until` (str, None) (optional): Will return a string that terminates with `read_until`, excluding `read_until`. 
        For example, if the string was `"abcdefg123456\\n"`, and `read_until` was `\\n`, then it will return `"abcdefg123456"`.
        If `read_until` is None, the it will return the entire string. By default None.
        - `strip` (bool) (optional): If True, then strips the received and processed string of whitespace and newlines, then 
        returns the result. If False, then returns the raw result. By default True.

        Returns:
        - `true` on success: The incoming received data matching `response`.
        - `false` on failure: Connection not established (if self.exception == False), incoming data did not match `response`, or `timeout` was reached, or send interval has not been reached.
        """

        if (not self._check_connect()):
            return False
        
        try:
            self.last_sent_outer # this is for the interval for calling send_for_response
        except AttributeError:
            # declare variable if not declared yet
            self.last_sent_outer = 0.0

        # check interval
        if (time.time() - self.last_sent_outer < self.send_interval):
            return False
        self.last_sent_outer = time.time()

        st_t = time.time() # for timeout

        while (True):
            if (time.time() - st_t > self.timeout):
                # timeout reached
                return False 
            
            self.send(*args, check_type=check_type, ending=ending, concatenate=concatenate)
            send_t = time.time()

            if (self.wait_for_response(response=response, after_timestamp=send_t, read_until=read_until, strip=strip)):
                return True

            time.sleep(0.01)
 
    def all_ports(self, **kwargs) -> t.Any:
        """Lists all available Serial ports.
        
        Calls `tools.all_ports()`, which itself calls `serial.tools.list_ports.comports()`.
        For more information, see [here](https://pyserial.readthedocs.io/en/latest/tools.html#module-serial.tools.list_ports).

        Parameters: none

        Returns: A generator-like object (see link above)
        """

        return tools.all_ports(**kwargs)
    
    def _check_connect(self) -> bool:
        """
        Checks if a connection has been established.
        Raises exception or returns false if not.
        """

        if (self.conn is None):
            if (self.exception):
                raise base_connection.ConnectException("No connection established")
            
            else:
                return False
        
        return True
    
    def _get_str(self, _call_time: float, read_until: t.Union[None, str], strip: bool = True) -> t.Union[str, None]:
        """
        `get()` but for strings
        """

        r = self.receive_str(read_until=read_until, strip=strip)

        if (r is None):
            return None

        st_t = time.time() # for timeout

        while (r[0] < _call_time):
            if (time.time() - st_t > self.timeout):
                # timeout reached
                return None 

            r = self.receive_str(read_until=read_until, strip=strip)
            time.sleep(0.01)
        
        # r received
        return r[1]
    
    def _get_bytes(self, _call_time: float) -> t.Union[bytes, None]:
        """
        `get()` but for bytes
        """

        r = self.receive()

        if (r is None):
            return None

        st_t = time.time() # for timeout

        while (r[0] < _call_time):
            if (time.time() - st_t > self.timeout):
                # timeout reached
                return None 

            r = self.receive()
            time.sleep(0.01)
        
        # r received
        return r[1]
    
    def _wait_for_response_str(self, response: str, timestamp: float, read_until: t.Union[str, None], strip: bool) -> bool:
        """
        `self._wait_for_response` but for strings
        """

        call_time = time.time() # call timestamp, for timeout

        r = self.receive_str(read_until=read_until, strip=strip)

        while (r is None or r[0] < timestamp or r[1] != response):
            # timestamp needs to be greater than start of method and response needs to match
            if (time.time() - call_time > self.timeout):
                # timeout reached
                return False 


            r = self.receive_str(read_until=read_until, strip=strip)
            time.sleep(0.01)
        
        # correct response has been received
        return True

    def _wait_for_response_bytes(self, response: bytes, timestamp: float) -> bool:
        """
        `self._wait_for_response` but for bytes
        """

        call_time = time.time() # call timestamp, for timeout
    
        r = self.receive()

        while (r is None or r[0] < timestamp or r[1] != response):
            # timestamp needs to be greater than start of method and response needs to match
            if (time.time() - call_time > self.timeout):
                # timeout reached
                return False
            
            r = self.receive()
            time.sleep(0.01)
        
        # correct response has been received
        return True
