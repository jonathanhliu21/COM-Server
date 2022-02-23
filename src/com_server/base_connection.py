#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Contains implementation of Connection object.
"""

import abc
import json
import os
import threading
import time
import typing as t
from types import TracebackType

import serial

from . import constants, tools

SEND_QUEUE_MAX_SIZE = 65536


class ConnectException(Exception):
    """
    Connecting/disconnecting errors
    """

    def __init__(self, msg: str) -> None:
        super().__init__(msg)


class BaseConnection(abc.ABC):
    """A base connection object with a serial or COM port.

    Base class that contains implemented basic methods: `send()`, `receive()`, `connect()`,
    and `disconnect()`, properties of the connection, and an abstract IO thread method.
    """

    def __init__(
        self,
        baud: int,
        port: str,
        *ports: str,
        exception: bool = True,
        timeout: float = 1,
        send_interval: float = 1,
        queue_size: int = constants.RCV_QUEUE_SIZE_NORMAL,
        exit_on_disconnect: bool = False,
        rest_cpu: bool = True,
        **kwargs: t.Any,
    ) -> None:
        """Initializes the Connection-like class.

        `baud`, `port` (or a port within `ports`), `timeout`, and `kwargs` will be passed to pyserial.
        For more information, see [here](https://pyserial.readthedocs.io/en/latest/pyserial_api.html#serial.Serial).

        Parameters:
            - `baud` (int): The baud rate of the serial connection
            - `port` (str): The serial port
            - `*ports`: Alternative serial ports to choose if the first port does not work. The program will try the serial ports in order of arguments and will use the first one that works.
            - `timeout` (float) (optional): How long the program should wait, in seconds, for serial data before exiting. By default 1.
            - `exception` (bool) (optional): (**DEPRECATED**) Raise an exception when there is a user error in the methods rather than just returning. By default True.
            - `send_interval` (float) (optional): Indicates how much time, in seconds, the program should wait before sending another message.
            Note that this does NOT mean that it will be able to send every `send_interval` seconds. It means that the `send()` method will
            exit if the interval has not reached `send_interval` seconds. NOT recommended to set to small values. By default 1.
            - `queue_size` (int) (optional): The number of previous data that was received that the program should keep. Must be nonnegative. By default 256.
            - `exit_on_disconnect` (bool) (optional): If True, sends `SIGTERM` signal to the main thread if the serial port is disconnected. Does NOT work on Windows. By default False.
            - `rest_cpu` (bool) (optional): If True, will add 0.01 second delay to end of IO thread. Otherwise, removes those delays but will result in increased CPU usage.
            Not recommended to set to False with the default IO thread. By default True.
            - `kwargs`: Will be passed to pyserial.

        Returns: nothing
        """

        # from above
        self._baud = int(baud)
        self._port = str(port)
        self._ports = ports
        self._ports_list = tuple([self._port] + list(self._ports))
        self._exception = bool(exception)
        self._timeout = abs(float(timeout))  # make sure positive
        self._pass_to_pyserial = kwargs
        self._queue_size = abs(int(queue_size))  # make sure positive
        self._send_interval = abs(float(send_interval))  # make sure positive
        self._exit_on_disconnect = exit_on_disconnect
        self._rest_cpu = rest_cpu

        if os.name == "nt" and self._exit_on_disconnect:
            raise EnvironmentError("exit_on_fail is not supported on Windows")

        # initialize Serial object
        self._conn: t.Optional[serial.Serial] = None

        # other
        self._last_sent = time.time()  # prevents from sending too rapidly
        self._last_rcv = (
            0.0,
            b"",
        )  # stores the data that the user previously received

        # IO variables
        self._rcv_queue: t.List[
            t.Tuple[float, bytes]
        ] = (
            []
        )  # stores previous received strings and timestamps, tuple (timestamp, str)
        self._to_send: t.List[bytes] = []  # queue data to send

        # this lock makes sure data from the receive queue
        # and send queue are written to and read safely
        self._lock = threading.Lock()

    def __repr__(self) -> str:
        """
        Returns string representation of self
        """

        return (
            f"Connection<id=0x{hex(id(self))}>"
            f"{{Serial={self._conn}, "
            f"timeout={self._timeout}, max_queue_size={self._queue_size}, send_interval={self._send_interval}}}"
        )

    def __enter__(self) -> "BaseConnection":
        """Context manager

        When in a context manager, it will automatically connect itself
        to its serial port and return itself.
        """

        if not self.connected:
            self.connect()

        return self

    def __exit__(
        self,
        exc_type: type,
        exc_value: BaseException,
        exc_tb: t.Optional[TracebackType],
    ) -> None:
        """Context manager

        When exiting from the `with` statement, it will automatically close itself.
        """

        self.disconnect()

    def connect(self) -> None:
        """Begins connection to the serial port.

        When called, initializes a serial instance if not initialized already. Also starts the IO thread.

        Parameters: None

        Returns: None
        """

        if self._conn is not None:
            if self._exception:
                # raise exception if true
                raise ConnectException("Connection already established")

            # return if initialized already
            return

        # timeout should be None in pyserial
        pyser_timeout = None if self._timeout == constants.NO_TIMEOUT else self._timeout

        # user-given ports
        _all_ports = self._ports_list
        # available ports
        _all_avail_ports = [port for port, _, _ in tools.all_ports()]

        # actual used port
        _used_port = "No port found"

        for port in _all_ports:
            if port in _all_avail_ports:
                _used_port = port
                break

        # set port attribute to new port (useful when printing)
        self._port = _used_port

        self._conn = serial.Serial(
            port=self._port,
            baudrate=self._baud,
            timeout=pyser_timeout,
            **self._pass_to_pyserial,
        )

        # clear buffers
        self._conn.flush()
        self._conn.flushInput()
        self._conn.flushOutput()

        time.sleep(2)  # wait for other end to start up properly

        # start receive thread
        threading.Thread(
            name="Serial-IO-thread", target=self._io_thread, daemon=True
        ).start()

    def disconnect(self) -> None:
        """Closes connection to the serial port.

        When called, calls `Serial.close()` then makes the connection `None`.
        If it is currently closed then just returns.
        Forces the IO thread to close.

        **NOTE**: This method should be called if the object will not be used anymore
        or before the object goes out of scope, as deleting the object without calling
        this will lead to stray threads.

        Parameters: None

        Returns: None
        """

        if self._conn is None:
            # return if not open, as threads are already closed
            return

        self._conn.close()
        self._reset()
        self._conn = None

    def send(
        self,
        *args: t.Any,
        check_type: bool = True,
        ending: str = "\r\n",
        concatenate: str = " ",
    ) -> bool:
        """Sends data to the port

        If the connection is open and the interval between sending is large enough,
        then concatenates args with a space (or what was given in `concatenate`) in between them,
        encodes to an `utf-8` `bytes` object, adds a carriage return and a newline to the end
        (i.e. "\\r\\n") (or what was given as `ending`), then sends to the serial port.

        Note that the data does not send immediately and instead will be added to a queue.
        The queue size limit is 65536 byte objects. Anything more that is trying to be sent will not be added to the queue.
        Sending data too rapidly (e.g. making `send_interval` too small, varies from computer to computer) is not recommended,
        as the queue will get too large and the send data will get backed up and will be delayed,
        since it takes a considerable amount of time for data to be sent through the serial port.
        Additionally, parts of the send queue will be all sent together until it reaches 0.5 seconds,
        which may end up with unexpected behavior in some programs.
        To prevent these problems, either make the value of `send_interval` larger,
        or add a delay within the main thread.

        If the program has not waited long enough before sending, then the method will return `false`.

        If `check_type` is True, then it will process each argument, then concatenate, encode, and send.
            - If the argument is `bytes` then decodes to `str`
            - If argument is `list` or `dict` then passes through `json.dumps`
            - If argument is `set` or `tuple` then converts to list and passes through `json.dumps`
            - Otherwise, directly convert to `str` and strip
        Otherwise, converts each argument directly to `str` and then concatenates, encodes, and sends.

        Parameters:
        - `*args`: Everything that is to be sent, each as a separate parameter. Must have at least one parameter.
        - `check_type` (bool) (optional): If types in *args should be checked. By default True.
        - `ending` (str) (optional): The ending of the bytes object to be sent through the serial port. By default a carraige return + newline ("\\r\\n")
        - `concatenate` (str) (optional): What the strings in args should be concatenated by. By default a space `' '`

        Returns:
        - `true` on success (everything has been sent through)
        - `false` on failure (not open, not waited long enough before sending, did not fully send through, etc.)
        """

        # check if connection open
        if self._conn is None:
            if self._exception:
                # raise exception if true
                raise ConnectException("No connection established")

            return False

        # check if it should send by using send_interval.
        if time.time() - self._last_sent <= self._send_interval:
            return False
        self._last_sent = time.time()

        # check `check_type`, then converts each element
        send_data: str = ""
        if check_type:
            send_data = concatenate.join([self._check_output(i) for i in args])
        else:
            send_data = concatenate.join([str(i) for i in args])

        # add ending to string
        send_data_bytes = (send_data + ending).encode("utf-8")

        # make sure nothing is reading/writing to the receive queue
        # while reading/assigning the variable
        with self._lock:
            if len(self._to_send) < SEND_QUEUE_MAX_SIZE:
                # only append if limit has not been reached
                self._to_send.append(send_data_bytes)

        return True

    def receive(self, num_before: int = 0) -> t.Optional[t.Tuple[float, bytes]]:
        """Returns the most recent receive object

        The IO thread will continuously detect receive data and put the `bytes` objects in the `rcv_queue`.
        If there are no parameters, the method will return the most recent received data.
        If `num_before` is greater than 0, then will return `num_before`th previous data.
            - Note: `num_before` must be less than the current size of the queue and greater or equal to 0
                - If not, returns None (no data)
            - Example:
                - 0 will return the most recent received data
                - 1 will return the 2nd most recent received data
                - ...

        Parameters:
        - `num_before` (int) (optional): Which receive object to return. Must be nonnegative. By default None.

        Returns:
        - A `tuple` representing the `(timestamp received, data in bytes)`
        - `None` if no data was found or port not open
        """

        if self._conn is None:
            if self._exception:
                # raise exception if true
                raise ConnectException("No connection established")

            return None

        if num_before < 0:
            # num before has to be nonnegative

            if self._exception:
                # raise exception if true
                raise ValueError("num_before has to be nonnegative")

            return None

        try:
            # make sure nothing is reading/writing to the receive queue
            # while reading/assigning the variable
            with self._lock:
                self._last_rcv = self._rcv_queue[-1 - num_before]  # last received data

            return self._last_rcv
        except IndexError:
            return None

    @property
    def connected(self) -> bool:
        """A property to determine if the connection object is currently connected to a serial port or not.

        This also can determine if the IO thread for this object
        is currently running or not.
        """

        return self._conn is not None

    @property
    def timeout(self) -> float:
        """A property to determine the timeout of this object.

        Getter:
        - Gets the timeout of this object.

        Setter:
        - Sets the timeout of this object after checking if convertible to nonnegative float.
        Then, sets the timeout to the same value on the `pyserial` object of this class.
        If the value is `float('inf')`, then sets the value of the `pyserial` object to None.
        """

        return self._timeout

    @timeout.setter
    def timeout(self, value: float) -> None:
        self._timeout = abs(float(value))

        if self._conn is not None:
            self._conn.timeout = (
                self._timeout if self._timeout != constants.NO_TIMEOUT else None
            )

    @property
    def send_interval(self) -> float:
        """A property to determine the send interval of this object.

        Getter:
        - Gets the send interval of this object.

        Setter:
        - Sets the send interval of this object after checking if convertible to nonnegative float.
        """

        return self._send_interval

    @send_interval.setter
    def send_interval(self, value: float) -> None:
        self._send_interval = abs(float(value))

    @property
    def conn_obj(self) -> serial.Serial:
        """A property to get the Serial object that handles sending and receiving.

        Getter:
        - Gets the Serial object.
        """

        return self._conn

    @property
    def available(self) -> int:
        """A property indicating how much new data there is in the receive queue.

        Getter:

        - Gets the number of additional data received since the user last called the `receive()` method.
        """

        if not self.connected:
            # check if connected
            if self._exception:
                raise ConnectException("No connection established")

            return 0

        last_rcv_ind = self._binary_search_rcv(self._last_rcv[0])

        return len(self._rcv_queue) - last_rcv_ind - 1

    @property
    def port(self) -> str:
        """Returns the current port of the connection

        Getter:

        - Gets the current port of the connection
        """

        return self._port

    def _check_output(self, output: t.Any) -> str:
        """Argument processing
        - If the argument is `bytes` then decodes to `str`
        - If argument is `list` or `dict` then passes through `json.dumps`
        - If argument is `set` or `tuple` then converts to list, passes through `json.dumps`
        - Otherwise, directly convert to `str`
        """

        ret = ""
        if isinstance(output, bytes):
            ret = output.decode("utf-8").strip()
        elif isinstance(output, list) or isinstance(output, dict):
            ret = json.dumps(output).strip()
        elif isinstance(output, tuple) or isinstance(output, set):
            ret = json.dumps(list(output)).strip()
        else:
            ret = str(output).strip()

        return ret

    def _reset(self) -> None:
        """
        Resets all IO variables
        """

        self._last_sent = time.time()  # prevents from sending too rapidly

        self._rcv_queue = []  # stores previous received strings
        self._to_send = []  # queue data to send

    def _binary_search_rcv(self, target: float) -> int:
        """
        Binary searches a timestamp in the receive queue and returns the index of that timestamp.

        Works because the timestamps in the receive queue are sorted by default.

        When comparing, rounds to 4 digits.
        """

        with self._lock:
            _tmp_q = self._rcv_queue.copy()

        if len(_tmp_q) <= 0:
            # not found if no size
            return -1

        low = 0
        high = len(_tmp_q)

        while low <= high:
            mid = (low + high) // 2  # integer division

            # comparing rounding to two digits
            cmp1 = round(_tmp_q[mid][0], 4)
            cmp2 = round(target, 4)

            if cmp1 == cmp2:
                return mid
            elif cmp1 < cmp2:
                low = mid + 1
            else:
                high = mid - 1

        # return -1 if not found
        return -1

    @abc.abstractmethod
    def _io_thread(self) -> None:
        """Thread that interacts with serial port.

        Implemented in `Connection` class.
        """
