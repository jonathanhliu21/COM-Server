#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Contains implementation of connection object.
"""

import os
import sys
import time
import typing as t
import serial
import signal

from serial.serialutil import SerialException

from . import base_connection, tools


class Connection(base_connection.BaseConnection):
    """A more user-friendly interface with the serial port.

    In addition to the four basic methods (see `BaseConnection`),
    it makes other methods that may also be useful to the user
    when communicating with the classes.

    Some of the methods include:
    - `get()`: Gets first response after the time that the method was called
    - `get_all_rcv()`: Returns the entire receive queue
    - `get_all_rcv_str()`: Returns the entire receive queue, converted to strings
    - `receive_str()`: Receives as a string rather than bytes object
    - `get_first_response()`: Gets the first response from the serial port after sending something (breaks when timeout reached)
    - `send_for_response()`: Continues sending something until the connection receives a given response (breaks when timeout reached)
    - `wait_for_response()`: Waits until the connection receives a given response (breaks when timeout reached)
    - `reconnect()`: Attempts to reconnect given a new port

    Other methods can generally help the user with interacting with the classes:
    - `all_ports()`: Lists all available COM ports.

    **Warning**: Before making this object go out of scope, make sure to call `disconnect()` in order to avoid thread leaks.
    If this does not happen, then the IO thread will still be running for an object that has already been deleted.
    """

    def __enter__(self) -> "Connection":
        """
        Same as `BaseConnection.__enter__()` but returns `Connection` object rather than a `BaseConnection` object.
        """

        if not self.connected:
            self.connect()

        return self

    def conv_bytes_to_str(
        self, rcv: bytes, read_until: t.Union[str, None] = None, strip: bool = True
    ) -> t.Union[str, None]:
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

        if rcv is None:
            return None

        res = rcv.decode("utf-8")

        try:
            ret = res[0 : res.index(str(read_until))]  # sliced string
            if strip:
                return ret.strip()
            else:
                return ret

        except (ValueError, TypeError):
            # read_until does not exist or it is None, so return the entire thing
            if strip:
                return res.strip()
            else:
                return res

    def get(
        self,
        given_type: t.Type,
        read_until: t.Union[str, None] = None,
        strip: bool = True,
    ) -> t.Union[None, bytes, str]:
        """Gets first response after this method is called.

        This method differs from `receive()` because `receive()` returns
        the last element of the receive buffer, which could contain objects
        that were received before this function was called. This function
        waits for something to be received after it is called until it either
        gets the object or until the timeout is reached.

        Parameters:
        - `given_type` (type): either `bytes` or `str`, indicating which one to return.
        Will raise exception if type is invalid, REGARDLESS of `self.exception`. Example: `get(str)` or `get(bytes)`.
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

        call_time = time.time()  # time that the function was called

        if given_type != str and given_type != bytes:
            raise TypeError("given_type must be literal 'str' or 'bytes'")

        if given_type == str:
            return self._get_str(call_time, read_until=read_until, strip=strip)
        else:
            return self._get_bytes(call_time)

    def get_all_rcv(self) -> "list[tuple[float, bytes]]":
        """Returns the entire receive queue

        The queue will be a `queue_size`-sized list that contains
        tuples (timestamp received, received bytes).

        Returns:
        - A list of tuples indicating the timestamp received and the bytes object received
        """

        return self._rcv_queue

    def get_all_rcv_str(
        self, read_until: t.Union[str, None] = None, strip: bool = True
    ) -> "list[tuple[float, str]]":
        """Returns entire receive queue as string.

        Each bytes object will be passed into `conv_bytes_to_str()`.
        This means that `read_until` and `strip` will apply to
        EVERY element in the receive queue before returning.

        Parameters:
        - `read_until` (str, None) (optional): Will return a string that terminates with `read_until`, excluding `read_until`.
        For example, if the string was `"abcdefg123456\\n"`, and `read_until` was `\\n`, then it will return `"abcdefg123456"`.
        If there are multiple occurrences of `read_until`, then it will return the string that terminates with the first one.
        If `read_until` is None or it doesn't exist, the it will return the entire string. By default None.
        - `strip` (bool) (optional): If True, then strips spaces and newlines from either side of the processed string before returning.
        If False, returns the processed string in its entirety. By default True.

        Returns:
        - A list of tuples indicating the timestamp received and the converted string from bytes
        """

        return [
            (ts, self.conv_bytes_to_str(rcv, read_until=read_until, strip=strip))
            for ts, rcv in self._rcv_queue
        ]

    def receive_str(
        self,
        num_before: int = 0,
        read_until: t.Union[str, None] = None,
        strip: bool = True,
    ) -> "t.Union[None, tuple[float, str]]":
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

        Note that the data will be read as ALL the data available in the serial port,
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
        if not self._check_connect():
            return None

        rcv_tuple = self.receive(num_before=num_before)
        if rcv_tuple is None:
            # return if None
            return None

        str_data = self.conv_bytes_to_str(
            rcv_tuple[1], read_until=read_until, strip=strip
        )

        return (rcv_tuple[0], str_data)

    def get_first_response(
        self,
        *args: "tuple[t.Any]",
        is_bytes: bool = True,
        check_type: bool = True,
        ending: str = "\r\n",
        concatenate: str = " ",
        read_until: t.Union[str, None] = None,
        strip: bool = True
    ) -> t.Union[bytes, str, None]:
        """Gets the first response from the serial port after sending something.

        This method works almost the same as `send()` (see `self.send()`).
        It also returns a string representing the first response from the serial port after sending.
        All `*args` and `check_type`, `ending`, and `concatenate`, will be sent to `send()`.

        If there is no response after reaching the timeout, then it breaks out of the method.

        Parameters:
        - `*args`: Everything that is to be sent, each as a separate parameter. Must have at least one parameter.
        - `is_bytes`: If False, then passes to `conv_bytes_to_str()` and returns a string
        with given options `read_until` and `strip`. See `conv_bytes_to_str()` for more details.
        If True, then returns raw `bytes` data. By default True.
        - `check_type` (bool) (optional): If types in *args should be checked. By default True.
        - `ending` (str) (optional): The ending of the bytes object to be sent through the serial port. By default a carraige return ("\\r\\n")
        - `concatenate` (str) (optional): What the strings in args should be concatenated by. By default a space `' '`.
        - `read_until` (str, None) (optional): Will return a string that terminates with `read_until`, excluding `read_until`.
        For example, if the string was `"abcdefg123456\\n"`, and `read_until` was `\\n`, then it will return `"abcdefg123456"`.
        If `read_until` is None, the it will return the entire string. By default None.
        - `strip` (bool) (optional): If True, then strips the received and processed string of whitespace and newlines, then
        returns the result. If False, then returns the raw result. By default True.

        Returns:
        - A string or bytes representing the first response from the serial port.
        - None if there was no connection (if self.exception == False), no data, timeout reached, or send interval not reached.
        """

        if not self._check_connect():
            return None

        send_time = time.time()  # tracks send time
        send_success = self.send(
            *args, check_type=check_type, ending=ending, concatenate=concatenate
        )

        # for receiving string or bytes
        rcv_func = self.receive if is_bytes else self.receive_str

        if not send_success:
            return None

        r = None
        if is_bytes:
            r = rcv_func()
        else:
            # strings have read_until option
            r = rcv_func(read_until=read_until, strip=strip)

        st = time.time()

        # compares send time to receive time; return the first receive object where the send time < receive time
        while r is None or r[0] < send_time:
            if time.time() - st > self._timeout:
                # reached timeout

                return None

            if is_bytes:
                r = rcv_func()
            else:
                # strings have read_until option
                r = rcv_func(read_until=read_until)

            time.sleep(0.05)

        return r[1]

    def wait_for_response(
        self,
        response: t.Union[str, bytes],
        after_timestamp: float = -1.0,
        read_until: t.Union[str, None] = None,
        strip: bool = True,
    ) -> bool:
        """Waits until the connection receives a given response.

        This method will call `receive()` repeatedly until it
        returns a string that matches `response` whose timestamp
        is greater than given timestamp (`after_timestamp`).

        Parameters:
        - `response` (str, bytes): The receive data that the program is looking for.
        If given a string, then compares the string to the response after it is decoded in `utf-8`.
        If given a bytes, then directly compares the bytes object to the response.
        If given anything else, converts to string.
        - `after_timestamp` (float) (optional): Look for responses that came after given time as the UNIX timestamp.
        If negative, the converts to time that the method was called, or `time.time()`. By default -1.0

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
        if after_timestamp < 0:
            # negative number to indicate program to use current time, time in parameter does not work
            after_timestamp = time.time()

        if isinstance(response, str):
            return self._wait_for_response_str(
                response, timestamp=after_timestamp, read_until=read_until, strip=strip
            )
        elif isinstance(response, bytes):
            return self._wait_for_response_bytes(response, timestamp=after_timestamp)
        else:
            return self._wait_for_response_str(
                str(response),
                timestamp=after_timestamp,
                read_until=read_until,
                strip=strip,
            )

    def send_for_response(
        self,
        response: t.Union[str, bytes],
        *args: "tuple[t.any]",
        read_until: t.Union[str, None] = None,
        strip: bool = True,
        check_type: bool = True,
        ending: str = "\r\n",
        concatenate: str = " "
    ) -> bool:
        """Continues sending something until the connection receives a given response.

        This method will call `send()` and `receive()` repeatedly (calls again if does not match given `response` parameter).
        See `send()` for more details on `*args` and `check_type`, `ending`, and `concatenate`, as these will be passed to the method.
        Will return `true` on success and `false` on failure (reached timeout)

        Parameters:
        - `response` (str, bytes): The receive data that the program looks for after sending.
        If given a string, then compares the string to the response after it is decoded in `utf-8`.
        If given a bytes, then directly compares the bytes object to the response.
        - `*args`: Everything that is to be sent, each as a separate parameter. Must have at least one parameter.
        - `check_type` (bool) (optional): If types in *args should be checked. By default True.
        - `ending` (str) (optional): The ending of the bytes object to be sent through the serial port. By default a carraige return ("\\r\\n")
        - `concatenate` (str) (optional): What the strings in args should be concatenated by. By default a space `' '`

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

        if not self._check_connect():
            return False

        try:
            self._last_sent_outer  # this is for the interval for calling send_for_response
        except AttributeError:
            # declare variable if not declared yet
            self._last_sent_outer = 0.0

        # check interval
        if time.time() - self._last_sent_outer < self._send_interval:
            return False
        self._last_sent_outer = time.time()

        st_t = time.time()  # for timeout

        while True:
            if time.time() - st_t > self._timeout:
                # timeout reached
                return False

            self.send(
                *args, check_type=check_type, ending=ending, concatenate=concatenate
            )

            if time.time() - st_t > self._timeout:
                # timeout reached
                return False

            send_t = time.time()

            if self.wait_for_response(
                response=response,
                after_timestamp=send_t,
                read_until=read_until,
                strip=strip,
            ):
                return True

            time.sleep(0.01)

    def reconnect(self, timeout: t.Union[float, None] = None) -> bool:
        """Attempts to reconnect the serial port.

        This method will continuously try to connect to the ports provided in `__init__()`
        until it reaches given `timeout` seconds. If `timeout` is None, then it will
        continuously try to reconnect indefinitely.

        Will raise `ConnectException` if already connected, regardless
        of if `exception` is True or not.

        Parameters:
        - `timeout` (float, None) (optional): Will try to reconnect for
        `timeout` seconds before returning. If None, then will try to reconnect
        indefinitely. By default None.

        Returns:
        - True if able to reconnect
        - False if not able to reconnect within given timeout
        """

        if self.connected:
            raise base_connection.ConnectException("Connection already established")

        st_t = time.time()

        while True:
            if timeout is not None and time.time() - st_t > timeout:
                # break if timeout reached
                return False

            try:
                self.connect()

                # able to connect
                return True
            except SerialException as e:
                # port not found
                time.sleep(0.01)  # rest CPU

    def all_ports(self, **kwargs) -> t.Any:
        """Lists all available serial ports.

        Calls `tools.all_ports()`, which itself calls `serial.tools.list_ports.comports()`.
        For more information, see [here](https://pyserial.readthedocs.io/en/latest/tools.html#module-serial.tools.list_ports).

        Parameters: See link above

        Returns: A generator-like object (see link above)
        """

        return tools.all_ports(**kwargs)

    def custom_io_thread(self, func) -> t.Callable:
        """A decorator custom IO thread rather than using the default one.

        It is recommended to read `pyserial`'s documentation before creating a custom IO thread.

        What the IO thread executes every 0.01 seconds will be referred to as a "cycle".

        Note that this method should be called **before** `connect()` is called, or
        else the thread will use the default cycle.

        To see the default cycle, see the documentation of `BaseConnection`.

        What the IO thread will do now is:

        1. Check if anything is using (reading from/writing to) the variables
        2. If not, copy the variables into a `SendQueue` and `ReceiveQueue` object.
        3. Call the `custom_io_thread` function (if none, calls the default cycle)
        4. Copy the results from the function back into the send queue and receive queue.
        5. Rest for 0.01 seconds to rest the CPU

        The cycle should be in a function that this decorator will be on top of.
        The function should accept three parameters:

        - `conn` (a `serial.Serial` object)
        - `rcv_queue` (a `ReceiveQueue` object; see more on how to use it in its documentation)
        - `send_queue` (a `SendQueue` object; see more on how to use it in its documentation)

        To enable autocompletion on your text editor, you can add type hinting:

        ```py
        from com_server import Connection, SendQueue, ReceiveQueue
        from serial import Serial

        conn = Connection(...)

        # some code

        @conn.custom_io_thread
        def custom_cycle(conn: Serial, rcv_queue: ReceiveQueue, send_queue: SendQueue):
            # code here

        conn.connect() # call this AFTER custom_io_thread()

        # more code
        ```

        The function below the decorator should not return anything.
        """

        self._cyc_func = func

        return func

    def _check_connect(self) -> bool:
        """
        Checks if a connection has been established.
        Raises exception or returns false if not.
        """

        if self._conn is None:
            if self._exception:
                raise base_connection.ConnectException("No connection established")

            else:
                return False

        return True

    def _get_str(
        self, _call_time: float, read_until: t.Union[None, str], strip: bool = True
    ) -> t.Union[str, None]:
        """
        `get()` but for strings
        """

        r = self.receive_str(read_until=read_until, strip=strip)

        st_t = time.time()  # for timeout

        # wait for r to not be None or for received time to be greater than call time
        while r is None or r[0] < _call_time:
            if time.time() - st_t > self._timeout:
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

        st_t = time.time()  # for timeout

        # wait for r to not be None or for received time to be greater than call time
        while r is None or r[0] < _call_time:
            if time.time() - st_t > self._timeout:
                # timeout reached
                return None

            r = self.receive()
            time.sleep(0.01)

        # r received
        return r[1]

    def _wait_for_response_str(
        self,
        response: str,
        timestamp: float,
        read_until: t.Union[str, None],
        strip: bool,
    ) -> bool:
        """
        `self._wait_for_response` but for strings
        """

        call_time = time.time()  # call timestamp, for timeout

        r = self.receive_str(read_until=read_until, strip=strip)

        while r is None or r[0] < timestamp or r[1] != response:
            # timestamp needs to be greater than start of method and response needs to match
            if time.time() - call_time > self._timeout:
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

        call_time = time.time()  # call timestamp, for timeout

        r = self.receive()

        while r is None or r[0] < timestamp or r[1] != response:
            # timestamp needs to be greater than start of method and response needs to match
            if time.time() - call_time > self._timeout:
                # timeout reached
                return False

            r = self.receive()
            time.sleep(0.01)

        # correct response has been received
        return True

    def _default_cycle(
        self,
        conn: serial.Serial,
        rcv_queue: tools.ReceiveQueue,
        send_queue: tools.SendQueue,
    ) -> None:
        """
        What the IO thread executes every 0.01 seconds will be referred to as a "cycle".

        This is the default "cycle" of the IO thread, described here:

        1. Checks if there is any data to be received
        2. If there is, reads all the data and puts the `bytes` received into the receive queue
        3. Tries to send everything in the send queue; breaks when 0.5 seconds is reached (will continue if send queue is empty)
        """

        # flush buffers
        self._conn.flush()

        # keep on trying to poll data as long as connection is still alive
        if conn.in_waiting:
            # read everything from serial buffer
            incoming = b""
            while conn.in_waiting:
                incoming += conn.read()

                if sys.platform.startswith("darwin"):
                    # fix partial data for small strings on MacOS
                    time.sleep(0.001)

            # add to queue
            rcv_queue.pushitems(incoming)

        # sending data (send one at a time in queue for 0.5 seconds)
        st_t = time.time()  # start time
        while time.time() - st_t < 0.5:
            if len(send_queue) > 0:
                conn.write(send_queue.front())  # write the front of the send queue
                conn.flush()
                send_queue.pop()  # pop the queue
            else:
                # break out if all sent
                break
            time.sleep(0.01)

    def _io_thread(self) -> None:
        """Thread that interacts with the serial port.

        What the IO thread executes every 0.01 seconds will be referred to as a "cycle".

        Override of the IO thread.

        Calls a function for executing a cycle rather than execute the default cycle itself.
        1. Check that the receive and send queues are not being read from or written to.
        2. If so, then copy the receive and send queues to another variable; if not,
        then wait for them to stop being used.
        3. Execute the cycle function.
        4. Check that the receive and send queues are not being read from or written to.
        5. If so, then copy the temporary receive/send queues back to the receive queue and send
        queue attributes; if not, then wait for them to stop being used.
        """

        # try to see if cycle function exists
        # if not, then use default cycle function
        try:
            self._cyc_func
        except AttributeError:
            self._cyc_func = self._default_cycle

        while self._conn is not None:
            try:
                # make sure other threads cannot read/write variables
                # copy the variables to temporary ones so the locks don't block for so long
                with self._lock:
                    _rcv_queue = tools.ReceiveQueue(
                        self._rcv_queue.copy(), self._queue_size
                    )
                    _send_queue = tools.SendQueue(self._to_send.copy())

                # find number of objects to send; important for pruning send queue later
                _num_to_send_i = len(_send_queue)

                self._cyc_func(self._conn, _rcv_queue, _send_queue)

                # find length of send queue after
                _num_to_send_f = len(_send_queue)

                # make sure other threads cannot read/write variables
                with self._lock:
                    # copy the variables back
                    self._rcv_queue = _rcv_queue.copy()

                    # delete the first element of send queue attribute for every object that was sent
                    # as those elements were the ones that were sent and are not needed anymore
                    for _ in range(_num_to_send_i - _num_to_send_f):
                        self._to_send.pop(0)

                time.sleep(0.01)  # rest CPU

            except (base_connection.ConnectException, OSError, serial.SerialException):
                # Disconnected, as all of the self.conn (pyserial) operations will raise
                # an exception if the port is not connected.

                # reset connection and IO variables
                self._conn = None
                self._reset()

                if self._exit_on_disconnect:
                    os.kill(os.getpid(), signal.SIGTERM)

                # exit thread
                return
