#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Contains implementation of Connection object.
"""

import json
import os
import signal
import threading
import time
import typing as t
from types import TracebackType

import serial


class ConnectException(Exception):
    """
    Connecting/disconnecting errors
    """

    def __init__(self, msg: str) -> None:
        super().__init__(msg)


class BaseConnection:
    """A base connection object with a serial or COM port.

    If you want to communicate via serial, it is recommended to
    either directly use `pyserial` directly or use the `Connection` class.

    How this works is that it creates a pyserial object given the parameters, which opens the connection. 
    The user can manually open and close the connection. It is closed by default when the initializer is called.
    It spawns a daemon thread that continuously looks for serial data and puts it in a buffer. 
    When the user wants to send something, it will pass the send data to a queue,
    and the thread will process the queue and will continuously send the contents in the queue
    until it is empty, or it has reached 0.5 seconds. This thread is referred as the "IO thread".

    All data will be encoded and decoded using `utf-8`.

    If used in a `while(true)` loop, it is highly recommended to put a `time.sleep()` within the loop,
    so the main thread won't use up so many resources and slow down the IO thread.

    This class contains the four basic methods needed to talk with the serial port:
    - `connect()`: opens a connection with the serial port
    - `disconnect()`: closes the connection with the serial port
    - `send()`: sends data to the serial port
    - `read()`: reads data from the serial port

    It also contains the property `connected` to indicate if it is currently connected to the serial port.

    If the USB port is disconnected while the program is running, then it will automatically detect the exception
    thrown by `pyserial`, and then it will reset the IO variables and then label itself as disconnected. It will
    then stop the IO thread. If `exit_on_disconnect` is True, it will send a `SIGTERM` signal to the main thread 
    if the port was disconnected.

    **Warning**: Before making this object go out of scope, make sure to call `disconnect()` in order to avoid thread leaks. 
    If this does not happen, then the IO thread will still be running for an object that has already been deleted.
    """

    def __init__(
        self, 
        baud: int, 
        port: str, 
        *args, 
        exception: bool = True, 
        timeout: float = 1, 
        send_interval: int = 1, 
        queue_size: int = 256, 
        exit_on_disconnect: bool = False, 
        **kwargs
        ) -> None:
        """Initializes the Base Connection class. 

        `baud`, `port`, `timeout`, and `kwargs` will be passed to pyserial.  
        For more information, see [here](https://pyserial.readthedocs.io/en/latest/pyserial_api.html#serial.Serial).

        Parameters:
            - `baud` (int): The baud rate of the serial connection 
            - `port` (str): The serial port
            - `timeout` (float) (optional): How long the program should wait, in seconds, for serial data before exiting. By default 1.
            - `exception` (bool) (optional): Raise an exception when there is a user error in the methods rather than just returning. By default True.
            - `send_interval` (int) (optional): Indicates how much time, in seconds, the program should wait before sending another message. 
            Note that this does NOT mean that it will be able to send every `send_interval` seconds. It means that the `send()` method will 
            exit if the interval has not reached `send_interval` seconds. NOT recommended to set to small values. By default 1.
            - `queue_size` (int) (optional): The number of previous data that was received that the program should keep. Must be nonnegative. By default 256.
            - `exit_on_disconnect` (bool) (optional): If True, sends `SIGTERM` signal to the main thread if the serial port is disconnected. Does NOT work on Windows. By default False.
            - `kwargs`: Will be passed to pyserial.

        Returns: nothing
        """

        # from above
        self.baud = int(baud)
        self.port = str(port)
        self.exception = bool(exception)
        self.timeout = abs(float(timeout))  # make sure positive
        self.pass_to_pyserial = kwargs
        self.queue_size = abs(int(queue_size))  # make sure positive
        self.send_interval = abs(float(send_interval))  # make sure positive
        self.exit_on_disconnect = exit_on_disconnect

        if (os.name == "nt" and self.exit_on_disconnect):
            raise EnvironmentError("exit_on_fail is not supported on Windows")

        # initialize Serial object
        self.conn = None

        # other
        self.last_sent = time.time()  # prevents from sending too rapidly

        self.rcv_queue = []  # stores previous received strings and timestamps, tuple (timestamp, str)
        self.to_send = [] # queue data to send

    def __repr__(self) -> str:
        """
        Returns string representation of self
        """

        return f"Connection<id=0x{hex(id(self))}>" \
            f"{{port={self.port}, baud={self.baud}, timeout={self.timeout}, queue_size={self.queue_size}, send_interval={self.send_interval}, " \
            f"Serial={self.conn}, " \
            f"last_sent={self.last_sent}, rcv_queue={str(self.rcv_queue)}, send_queue={str(self.to_send)}}}"

    def __enter__(self) -> "BaseConnection":
        """Context manager

        When in a context manager, it will automatically connect itself
        to its serial port and return itself. 
        """
        
        if (not self.connected):
            self.connect()
        
        return self
    
    def __exit__(self, exc_type: type, exc_value: BaseException, exc_tb: t.Union[None, TracebackType]) -> None:
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

        if (self.conn is not None):
            if (self.exception):
                # raise exception if true
                raise ConnectException("Connection already established")

            # return if initialized already
            return

        self.conn = serial.Serial(
            port=self.port, baudrate=self.baud, timeout=self.timeout, **self.pass_to_pyserial)

        time.sleep(2)  # wait for other end to start up properly

        # start receive thread
        threading.Thread(name="Serial-IO-thread", target=self._io_thread, daemon=True).start()

    def disconnect(self) -> None:
        """Closes connection to the serial port.

        When called, calls `Serial.close()` then makes the connection `None`. If it is currently closed then just returns.
        
        **NOTE**: This method should be called if the object will not be used anymore
        or before the object goes out of scope, as deleting the object without calling 
        this will lead to stray threads.

        Parameters: None

        Returns: None
        """

        if (self.conn is None):
            # return if not open, as threads are already closed
            return

        self.conn.close()
        self._reset()
        self.conn = None

    def send(self, *args: "tuple[t.Any]", check_type: bool = True, ending: str = "\r\n", concatenate: str = ' ') -> bool:
        """Sends data to the port

        If the connection is open and the interval between sending is large enough, 
        then concatenates args with a space (or what was given in `concatenate`) in between them, 
        encodes to an `utf-8` `bytes` object, adds a carriage return and a newline to the end (i.e. "\\r\\n") (or what was given as `ending`), then sends to the serial port.

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
        if (self.conn is None):
            if (self.exception):
                # raise exception if true
                raise ConnectException("No connection established")

            return False

        # check if it should send by using send_interval.
        if (time.time() - self.last_sent <= self.send_interval):
            return False
        self.last_sent = time.time()

        # check `check_type`, then converts each element
        send_data = []
        if (check_type):
            send_data = concatenate.join([self._check_output(i) for i in args])
        else:
            send_data = concatenate.join([str(i) for i in args])

        # add ending to string
        send_data = (send_data + ending).encode("utf-8")

        if (len(self.to_send) < 65536):
            # only append if limit has not been reached
            self.to_send.append(send_data)
        
        return True

    def receive(self, num_before: int = 0) -> "t.Union[tuple[float, bytes], None]":
        """Returns the most recent receive object

        The IO thread will continuously detect receive data and put the `bytes` objects in the `rcv_queue`. 
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

        Parameters:
        - `num_before` (int) (optional): Which receive object to return. Must be nonnegative. By default None.

        Returns:
        - A `tuple` representing the `(timestamp received, data in bytes)`
        - `None` if no data was found or port not open
        """

        if (self.conn is None):
            if (self.exception):
                # raise exception if true
                raise ConnectException("No connection established")

            return None

        if (num_before < 0):
            # num before has to be nonnegative

            if (self.exception):
                # raise exception if true
                raise ValueError("num_before has to be nonnegative")

            return None
        
        try:
            return self.rcv_queue[-1-num_before]
        except IndexError as e:
            return None
 
    @property
    def connected(self) -> bool:
        """A property to determine if the connection object is currently connected to a serial port or not.

        This also can determine if the IO thread for this object
        is currently running or not.
        """

        return self.conn is not None

    def _check_output(self, output: str) -> str:
        """Argument processing
            - If the argument is `bytes` then decodes to `str`
            - If argument is `list` or `dict` then passes through `json.dumps`
            - If argument is `set` or `tuple` then converts to list, passes through `json.dumps`
            - Otherwise, directly convert to `str` 
        """

        ret = ""
        if (isinstance(output, bytes)):
            ret = output.decode("utf-8").strip()
        elif (isinstance(output, list) or isinstance(output, dict)):
            ret = json.dumps(output).strip()
        elif (isinstance(output, tuple) or isinstance(output, set)):
            ret = json.dumps(list(output)).strip()
        else:
            ret = str(output).strip()

        return ret

    def _io_thread(self) -> None:
        """Thread that interacts with serial port.

        Will continuously read data and add bytes to queue (`rcv_queue`).
        Will also take send queue (`to_send`) and send contents one at a time.
        """

        while (self.conn is not None):
            try:
                # keep on trying to poll data as long as connection is still alive
                if (self.conn.in_waiting):
                    # read everything from serial buffer
                    incoming = self.conn.read_all()

                    # add to queue
                    self.rcv_queue.append((time.time(), incoming)) # tuple (timestamp, str)
                    if (len(self.rcv_queue) > self.queue_size):
                        # if greater than queue size, then pop first element
                        self.rcv_queue.pop(0)
                
                # sending data (send one at a time in queue for 0.5 seconds)
                st_t = time.time() # start time
                while (time.time() - st_t < 0.5):
                    if (len(self.to_send) > 0):
                        self.conn.write(self.to_send.pop(0))
                        self.conn.flush()
                    else:
                        # break out if all sent
                        break
                    time.sleep(0.01)

                time.sleep(0.01)  # rest CPU
            except (ConnectException, OSError, serial.SerialException):
                # Disconnected, as all of the self.conn (pyserial) operations will raise
                # an exception if the port is not connected.

                # reset connection and IO variables
                self.conn = None
                self._reset()

                if (self.exit_on_disconnect):
                    os.kill(os.getpid(), signal.SIGTERM)
                
                # exit thread
                return

    def _reset(self) -> None:
        """
        Resets all IO variables
        """

        self.last_sent = time.time()  # prevents from sending too rapidly

        self.rcv_queue = []  # stores previous received strings
        self.to_send = [] # queue data to send
