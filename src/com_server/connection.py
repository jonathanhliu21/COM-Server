#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Contains implementation of connection object.
"""

import copy
import os
import signal
import time
import typing as t

import serial
from serial.serialutil import SerialException

from .base_connection import BaseConnection, ConnectException
from .tools import ReceiveQueue, SendQueue

if os.name == "posix":
    import termios


class Connection(BaseConnection):
    """Class that interfaces with the serial port.

    **Warning**: Before making this object go out of scope, make sure to call `disconnect()` in order to avoid zombie threads.
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
        self,
        rcv: t.Optional[bytes],
        read_until: t.Optional[str] = None,
        strip: bool = True,
    ) -> t.Optional[str]:
        """Converts bytes object to string given parameters

        Args:
            rcv (bytes, None): A bytes object. If None, then the method will return None.
            read_until (bytes, None, optional): Will return a string that terminates with `read_until`, excluding `read_until`. \
            For example, if the string is `"abcdefg123456]"`, and `read_until` is `]`, then it will return `"abcdefg123456"`. \
            If there are multiple occurrences of `read_until`, then it will return the string that terminates with the first one. \
            If None, the it will return the entire string. Defaults to None.
            strip (bool, optional): If True, then strips spaces and newlines from either side of the processed string before returning. \
            If False, returns the processed string in its entirety. Defaults to True.

        Returns:
            Optional[str]: A string representing the processed data, or None if `rcv` is None
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
        return_bytes: bool = False,
        read_until: t.Optional[str] = None,
        strip: bool = True,
    ) -> t.Optional[t.Union[bytes, str]]:
        """Gets first response after this method is called.

        This method waits for an object to be received from the serial
        port and returns that object. If the timeout is reached while
        waiting, then this method will return None.

        Args:
            return_bytes (bool, optional): Will return bytes if True and string if False. If true, other args will be ignored. Defaults to False.
            read_until (bytes, None, optional): Will return a string that terminates with `read_until`, excluding `read_until`. \
            For example, if the string is `"abcdefg123456]"`, and `read_until` is `]`, then it will return `"abcdefg123456"`. \
            If there are multiple occurrences of `read_until`, then it will return the string that terminates with the first one. \
            If None, the it will return the entire string. Defaults to None.
            strip (bool, optional): If True, then strips spaces and newlines from either side of the processed string before returning. \
            If False, returns the processed string in its entirety. Defaults to True.

        Raises:
            ConnectException: If serial port not connected, this exception will be raised.

        Returns:
            Optional[Union[bytes, str]]: A bytes or a processed string (depending on `return_bytes`) representing the first object \
                received from the serial port. None if no object received.
        """

        if not self.connected:
            raise ConnectException("No connection established")

        call_time = time.time()  # time that the function was called

        r: t.Optional[t.Tuple[float, t.Union[bytes, str]]] = None
        if return_bytes:
            r = self.receive()
        else:
            r = self.receive_str(read_until=read_until, strip=strip)

        st_t = time.time()  # for timeout

        # wait for r to not be None or for received time to be greater than call time
        while r is None or r[0] < call_time:
            if time.time() - st_t > self._timeout:
                # timeout reached
                return None

            if return_bytes:
                r = self.receive()
            else:
                r = self.receive_str(read_until=read_until, strip=strip)
            time.sleep(0.01)

        # r received
        return r[1]

    def all_rcv(
        self,
        return_bytes: bool = False,
        read_until: t.Optional[str] = None,
        strip: bool = True,
    ) -> t.Union[t.List[t.Tuple[float, str]], t.List[t.Tuple[float, bytes]]]:
        """Returns entire receive queue

        Args:
            return_bytes (bool, optional): Will return bytes if True and string if False. If true, other args will be ignored. Defaults to False.
            read_until (bytes, None, optional): All strings in the list will terminate with `read_until` without the `read_until` character. \
            For example, if a string in the list was `"abcdefg123456]"`, and `read_until` is `]`, then the string will become `"abcdefg123456"`. \
            If None, the it will return the entire string. Defaults to None.
            strip (bool, optional): If True, then strips spaces and newlines from either side of the processed string before returning. \
            If False, returns the processed string in its entirety. Defaults to True.

        Raises:
            ConnectException: If serial port not connected, this exception will be raised.

        Returns:
            Union[List[Tuple[float, str]], List[Tuple[float, bytes]]]: A list of tuples indicating the timestamp received and the converted string from bytes if `return_bytes` \
                is false, otherwise a list of tuples indicating the timestamp received and bytes object from serial port.
        """

        if not self.connected:
            raise ConnectException("No connection established")

        with self._lock:
            _rq = copy.deepcopy(self._rcv_queue)

        # _rq is a copy of receive queue, meaning that it is in bytes
        if return_bytes:
            return _rq

        ret: t.List[t.Tuple[float, str]] = []

        for ts, rcv in _rq:
            to_str = self.conv_bytes_to_str(rcv, read_until=read_until, strip=strip)
            assert to_str  # mypy

            ret.append((ts, to_str))

        return ret

    def receive_str(
        self,
        num_before: int = 0,
        read_until: t.Optional[str] = None,
        strip: bool = True,
    ) -> t.Optional[t.Tuple[float, str]]:
        """Returns the most recently received object as a processed string.

        To get the bytes object, use `Connection.receive()`.

        The IO thread will continuously detect data from the serial port and put the `bytes` objects in the `rcv_queue`.
        If there are no parameters, the method will return the most recent received data.
        If `num_before` is greater than 0, then will return `num_before`th previous data.
            - Note: Must be less than the current size of the queue and greater or equal to 0
                - If not, returns None (no data)
            - Example:
                - 0 will return the most recent received data
                - 1 will return the 2nd most recent received data
                - ...

        Args:
            num_before (int, optional): The position in the receive queue to return data from. Defaults to 0.
            read_until (bytes, None, optional): Will return a string that terminates with `read_until`, excluding `read_until`. \
            For example, if the string is `"abcdefg123456]"`, and `read_until` is `]`, then it will return `"abcdefg123456"`. \
            If there are multiple occurrences of `read_until`, then it will return the string that terminates with the first one. \
            If None, the it will return the entire string. Defaults to None.
            strip (bool, optional): If True, then strips spaces and newlines from either side of the processed string before returning. \
            If False, returns the processed string in its entirety. Defaults to True.

        Raises:
            ConnectException: If serial port not connected, this exception will be raised.

        Returns:
            Optional[Tuple[float, str]]: A `tuple` representing `(timestamp received, string data)` and None if no data was found
        """

        if not self.connected:
            raise ConnectException("No connection established")

        rcv_tuple = self.receive(num_before=num_before)
        if rcv_tuple is None:
            # return if None
            return None

        str_data = self.conv_bytes_to_str(
            rcv_tuple[1], read_until=read_until, strip=strip
        )

        if not str_data:
            # mypy
            return None

        return (rcv_tuple[0], str_data)

    def get_first_response(
        self,
        *data: t.Any,
        return_bytes: bool = False,
        ending: str = "\r\n",
        concatenate: str = " ",
        read_until: t.Optional[str] = None,
        strip: bool = True
    ) -> t.Optional[t.Union[str, bytes]]:
        """Gets the first response from the serial port after sending something.

        Args:
            *data (Any): Everything that is to be sent, each as a separate parameter. Must have at least one parameter.
            return_bytes (bool, optional): Will return bytes if True and string if False. If true, other args will be ignored. Defaults to False.
            ending (str, optional): The ending of the bytes object to be sent through the serial port. Defaults to "\\r\\n".
            concatenate (str, optional): What the strings in args should be concatenated by. Defaults to a space (" ").
            read_until (bytes, None, optional): Will return a string that terminates with `read_until`, excluding `read_until`. \
            For example, if the string is `"abcdefg123456]"`, and `read_until` is `]`, then it will return `"abcdefg123456"`. \
            If there are multiple occurrences of `read_until`, then it will return the string that terminates with the first one. \
            If None, the it will return the entire string. Defaults to None.
            strip (bool, optional): If True, then strips spaces and newlines from either side of the processed string before returning. \
            If False, returns the processed string in its entirety. Defaults to True.

        Raises:
            ConnectException: If serial port not connected, this exception will be raised.

        Returns:
            Optional[Union[bytes, str]]: A bytes or a processed string (depending on `return_bytes`) representing the first object \
                received from the serial port. None if no object received.
        """

        if not self.connected:
            raise ConnectException("No connection established")

        send_success = self.send(
            *data, check_type=True, ending=ending, concatenate=concatenate
        )

        if not send_success:
            # send interval not reached
            return None

        return self.get(return_bytes, read_until, strip)

    def wait_for_response(
        self,
        response: t.Any,
        after_timestamp: float = -1.0,
        read_until: t.Optional[str] = None,
        strip: bool = True,
    ) -> bool:
        """Waits until the connection receives a given response.

        This method will wait for a response that matches given `response`
        whose time received is greater than given timestamp `after_timestamp`.

        Args:
            response (Any): The receive data that the program is looking for. \
            If given a string, then compares the string to the response after it is decoded in `utf-8`. \
            If given a bytes, then directly compares the bytes object to the response. \
            If given anything else, converts to string.
            after_timestamp (float, optional): Look for responses that came after given time as the UNIX timestamp. \
            If negative, the converts to time that the method was called, or `time.time()`. Defaults to -1.0.
            read_until (bytes, None, optional): Will return a string that terminates with `read_until`, excluding `read_until`. \
            For example, if the string is `"abcdefg123456]"`, and `read_until` is `]`, then it will return `"abcdefg123456"`. \
            If there are multiple occurrences of `read_until`, then it will return the string that terminates with the first one. \
            If None, the it will return the entire string. Defaults to None.
            strip (bool, optional): If True, then strips spaces and newlines from either side of the processed string before returning. \
            If False, returns the processed string in its entirety. Defaults to True.

        Raises:
            ConnectException: If serial port not connected, this exception will be raised.

        Returns:
            bool: True on success and False if timeout reached because response has not been received.
        """

        if not self.connected:
            raise ConnectException("No connection established")

        after_timestamp = float(after_timestamp)
        if after_timestamp < 0:
            # negative number to indicate program to use current time, time in parameter does not work
            after_timestamp = time.time()

        # convert non-bytes to str
        if not isinstance(response, bytes):
            response = str(response)

        call_time = time.time()  # for timeout

        r: t.Optional[t.Tuple[float, t.Union[bytes, str]]] = None
        if isinstance(response, bytes):
            r = self.receive()
        else:
            r = self.receive_str(read_until=read_until, strip=strip)

        # continue searching until receive object has timestamp greater than after_timestamp
        # and response matches
        while r is None or r[0] < after_timestamp or r[1] != response:
            # timestamp needs to be greater than start of method and response needs to match
            if time.time() - call_time > self._timeout:
                # timeout reached
                return False

            if isinstance(response, bytes):
                r = self.receive()
            else:
                r = self.receive_str(read_until=read_until, strip=strip)

            time.sleep(0.01)

        # correct response has been received
        return True

    def send_for_response(
        self,
        response: t.Any,
        *data: t.Any,
        read_until: t.Optional[str] = None,
        strip: bool = True,
        ending: str = "\r\n",
        concatenate: str = " "
    ) -> bool:
        """Sends something until the connection receives a given response or timeout is reached.

        Args:
            response (Any): The receive data that the program is looking for. \
            If given a string, then compares the string to the response after it is decoded in `utf-8`. \
            If given a bytes, then directly compares the bytes object to the response. \
            If given anything else, converts to string.
            *data (Any): Everything that is to be sent, each as a separate parameter. Must have at least one parameter.
            ending (str, optional): The ending of the bytes object to be sent through the serial port. Defaults to "\\r\\n".
            concatenate (str, optional): What the strings in args should be concatenated by. Defaults to a space (" ").
            read_until (bytes, None, optional): Will return a string that terminates with `read_until`, excluding `read_until`. \
            For example, if the string is `"abcdefg123456]"`, and `read_until` is `]`, then it will return `"abcdefg123456"`. \
            If there are multiple occurrences of `read_until`, then it will return the string that terminates with the first one. \
            If None, the it will return the entire string. Defaults to None.
            strip (bool, optional): If True, then strips spaces and newlines from either side of the processed string before returning. \
            If False, returns the processed string in its entirety. Defaults to True.

        Raises:
            ConnectException: If serial port not connected, this exception will be raised.

        Returns:
            bool: True on success and False if timeout reached because response has not been received.
        """

        if not self.connected:
            raise ConnectException("No connection established")

        st_t = time.time()  # for timeout

        while True:
            if time.time() - st_t > self._timeout:
                # timeout reached
                return False

            self.send(*data, ending=ending, concatenate=concatenate)

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

    def reconnect(self, timeout: t.Optional[float] = None) -> bool:
        """Attempts to reconnect the serial port.

        This method will continuously try to connect to the ports provided in `__init__()`
        until it reaches given `timeout` seconds. If `timeout` is None, then it will
        continuously try to reconnect indefinitely.

        Args:
            timeout (float, None, optional): Will try to reconnect for \
            `timeout` seconds before returning. If None, then will try to reconnect \
            indefinitely. Defaults to None.

        Raises:
            ConnectException: Raised if already connected.

        Returns:
            bool: true if able to reconnect and false if not able to reconnect within timeout
        """

        if self.connected:
            raise ConnectException("Connection already established")

        st_t = time.time()

        while True:
            if timeout is not None and time.time() - st_t > timeout:
                # break if timeout reached
                return False

            if os.name == "posix":
                # may raise termios.error
                try:
                    self.connect()

                    # able to connect
                    return True
                except (SerialException, termios.error):
                    # port not found
                    time.sleep(0.1)  # rest CPU
            else:
                try:
                    self.connect()

                    # able to connect
                    return True
                except SerialException:
                    # port not found
                    time.sleep(0.01)  # rest CPU

    def custom_io_thread(self, func: t.Callable) -> t.Callable:
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

    def _default_cycle(
        self,
        conn: serial.Serial,
        rcv_queue: ReceiveQueue,
        send_queue: SendQueue,
    ) -> None:
        """
        What the IO thread executes every 0.01 seconds will be referred to as a "cycle".

        This is the default "cycle" of the IO thread, described here:

        1. Checks if there is any data to be received
        2. If there is, reads all the data and puts the `bytes` received into the receive queue
        3. Tries to send everything in the send queue; breaks when 0.5 seconds is reached (will continue if send queue is empty)
        """

        # flush buffers
        conn.flush()

        # keep on trying to poll data as long as connection is still alive
        if conn.in_waiting:
            # read everything from serial buffer
            incoming = b""
            while conn.in_waiting:
                incoming += conn.read()
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

    def _cyc(self) -> None:
        """
        Each cycle of the IO thread
        """
        # make sure other threads cannot read/write variables
        # copy the variables to temporary ones so the locks don't block for so long
        with self._lock:
            _rcv_queue = ReceiveQueue(self._rcv_queue.copy(), self._queue_size)
            _send_queue = SendQueue(self._to_send.copy())

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

        if self._rest_cpu:
            time.sleep(0.01)  # rest CPU

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
            if os.name == "posix":
                # may raise termios.error, not on Windows

                try:
                    self._cyc()
                except (
                    ConnectException,
                    OSError,
                    serial.SerialException,
                    termios.error,
                ):
                    # Disconnected, as all of the self.conn (pyserial) operations will raise
                    # an exception if the port is not connected.

                    # reset connection and IO variables
                    self._conn = None
                    self._reset()

                    if self._exit_on_disconnect:
                        os.kill(os.getpid(), signal.SIGTERM)

                    # exit thread
                    return
            else:
                try:
                    self._cyc()
                except (
                    ConnectException,
                    OSError,
                    serial.SerialException,
                ):
                    # Disconnected, as all of the self.conn (pyserial) operations will raise
                    # an exception if the port is not connected.

                    # reset connection and IO variables
                    self._conn = None
                    self._reset()

                    if self._exit_on_disconnect:
                        os.kill(os.getpid(), signal.SIGTERM)

                    # exit thread
                    return
