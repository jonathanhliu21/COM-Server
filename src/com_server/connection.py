#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Contains implementation of Connection object.
"""

import json
import time
import threading
import typing as t

import serial

class BaseConnection:
    """A base connection object with a Serial port.

    If you want to talk with the Arduino via Serial, 
    either directly use `pyserial` directly or use the `Connection` class.

    How this works is that it creates a pyserial object given the parameters, which opens the connection. 
    The user can manually open and close the connection. It is closed by default when the initializer is called.
    It spawns a thread that continuously looks for serial data and puts it in a buffer. 
    When the user wants to send, it will interrupt the getting of data and send the data, 
    then resume the getting of data. 

    This class contains the four basic functions needed to talk with the serial port:
    - `connect()`: opens a connection with the serial port
    - `disconnect()`: closes the connection with the serial port
    - `send()`: sends data to the serial port
    - `read()`: reads data from the serial port
    """

    def __init__(self, baud: int, port: str, *args, timeout: float = 1, send_interval: int = 1, queue_size: int = 256, **kwargs) -> None:
        """Initializes the Connection class. 

        `baud`, `port`, `timeout`, and `kwargs` will be passed to pyserial.  

        Parameters:
            - `baud` (int): The baud rate of the Serial connection 
            - `port` (str): The serial port
            - `timeout` (float) (optional): How long the program should wait, in seconds, for Serial data before exiting. By default 1.
            - `send_interval` (int) (optional): Indicates how much time, in seconds, the program should wait before sending another message. 
            Not that this does NOT mean that it will be able to send every `send_interval` seconds. It means that the `send()` function will 
            exit if the interval has not reached `send_interval` seconds. By default 1.
            - `queue_size` (int) (optional): The number of previous receives that the program should keep. Must be nonnegative. By default 256.
            - `kwargs`: Will be passed to pyserial
        
        Returns: nothing
        """

        # from above
        self.baud = int(baud)
        self.port = str(port)
        self.timeout = abs(float(timeout)) # make sure positive
        self.pass_to_pyserial = kwargs
        self.queue_size = abs(int(queue_size)) # make sure positive
        self.send_interval = abs(int(send_interval)) # make sure positive

        # initialize Serial object
        self.conn = None

        # other
        self.last_sent = time.time() # prevents from sending too rapidly

        self.rcv_queue = [] # stores previous received strings
        self.busy = False # to make thread-safe; indicates if Serial port is currently being used, threads will wait until this is False until doing operations

    def __repr__(self) -> str:
        """Returns string representation of self
        """

        return f"Connection<id=0x{hex(id(self))}, " \
            f"{{port={self.port}, baud={self.baud}, timeout={self.timeout}, queue_size={self.queue_size}, send_interval={self.send_interval}, " \
            f"Serial={self.conn}, " \
            f"last_sent={self.last_sent}, rcv_queue={str(self.rcv_queue)}, busy={self.busy}}}" 
    
    def connect(self) -> None:
        """Begins connection to the Serial port.

        When called, initializes a Serial instance if not initialized already. Also starts the receive thread.

        Parameters: None

        Returns: None
        """

        if (self.conn is not None):
            # return if initialized already
            return

        self.conn = serial.Serial(port=self.port, baudrate=self.baud, timeout=self.timeout, **self.pass_to_pyserial)

        time.sleep(2) # wait for other end to start up properly

        # start receive thread
        threading.Thread(target=self._rcv_thread, daemon=True).start()
    
    def disconnect(self) -> None:
        """Closes connection to the Serial port.

        When called, calls `Serial.close()` then makes the connection `None`. If it is currently, closed, then just returns.

        Parameters: None

        Returns: None
        """

        if (self.conn is None):
            # return if not open
            return
        
        self.conn.close()
        self._reset()
        self.conn = None
        
    def send(self, *args: "tuple[t.Any]", check_type: bool = True, ending: str = "\r\n", concatenate: str = ' ') -> bool:
        """Sends data to the port

        If the connection is open and the interval between sending is large enough, 
        then concatenates args with a space (or what was given in `concatenate`) in between them, 
        encodes to `utf-8` `bytes` object, adds carriage return to the end ("\\r\\n") (or what was given as `ending`), then sends.

        If the interval is too small, then what will most likely happen is that the program will delay anyways
        because it will wait for the receive thread to finish receiving its data before continuing.

        If the program has not waited long enough before sending, then the function will return `false`.

        If `check_type` is True, then it will process each argument, then concatenate, encode, and send.
            - If the argument is `bytes` then decodes to `str`
            - If argument is `list` or `dict` then passes through `json.dumps`
            - If argument is `set` or `tuple` then converts to list, passes through `json.dumps`
            - Otherwise, directly convert to `str` and strip
        Otherwise, converts each argument directly to `str` and then concatenates, encodes, and sends.

        Parameters:
        - `*args`: Everything that is to be sent, each as a separate parameter. Must have at least one parameter.
        - `check_type` (bool) (optional): If types in *args should be checked. By default True.
        - `ending` (str) (optional): The ending of the bytes object to be sent through the Serial port. By default a carraige return ("\\r\\n")
        - `concatenate` (str) (optional): What the strings in args should be concatenated by

        Returns:
        - `true` on success (everything has been sent through)
        - `false` on failure (not open, not waited long enough before sending, did not fully send through, etc.)
        """

        # check if connection open
        if (self.conn is None):
            return False
        
        # check `check_type`, then converts each element
        send_data = []
        if (check_type):
            send_data = concatenate.join([self._check_output(i) for i in args])
        else:
            send_data = concatenate.join([str(i) for i in args])

        # add ending to string
        send_data = (send_data + ending).encode("utf-8")

        # wait until serial port is not busy, then make busy and send
        while (self.busy):
            time.sleep(0.01)
        
        # check if it should send by using send_interval.
        if (time.time() - self.last_sent <= self.send_interval):
            return False
        
        self.busy = True

        # check that the timeout has not been reached by comparing current time to time before send
        tm_bf_send = time.time()
        self.conn.write(send_data) # write data
        self.conn.flush()

        # unset busy
        self.last_sent = time.time()
        self.busy = False

        if (time.time() - tm_bf_send >= self.timeout):
            # timeout reached, return False
            time.sleep(0.1) # give time to make receive thread get data
            return False

        if (self.send_interval < 0.1):  
            time.sleep(0.1) # give time to make receive thread get data

        return True

    def receive(self, num_before: int = 0) -> t.Union[str, None]:
        """Returns the most recent receive object

        The receive thread will continuously detect receive data and put it in the `rcv_queue`. 
        If there are no parameters, the function will return the most recent received data.
        If `num_before` is greater than 0, then will return `num_before`th previous data.
            - Note: Must be less than the current size of the queue and greater or equal to 0 
                - If not, returns None (no data)
            - Example:
                - 0 will return the most recent received data
                - 1 will return the 2nd most recent received data
                - ...
        
        Parameters:
        - `num_before` (int) (optional): Which receive object to return

        Returns:
        - A string representing the data
        - `None` if no data was found or port not open
        """

        if (self.conn is None):
            return None

        if (num_before < 0):
            # num before has to be nonnegative
            return None

        try:
            return self.rcv_queue[-1-num_before]
        except IndexError:
            return None
    
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
    
    def _rcv_thread(self) -> None:
        """Thread that continuously reads incoming data from Serial port.
        """

        while (self.conn is not None):
            # keep on trying to poll data as long as connection is still alive
            if (self.conn.in_waiting):
                while (self.busy):
                    # wait for all operations to finish
                    time.sleep(0.01)

                self.busy = True
                incoming = self.conn.readall().decode("utf-8")

                self.rcv_queue.append(incoming)
                if (len(self.rcv_queue) > self.queue_size):
                    # if greater than queue size, then pop first element
                    self.rcv_queue.pop(0)
 
            self.busy = False 
            time.sleep(0.1) # give others time to process write data
    
    def _reset(self) -> None:
        """Resets all IO variables
        """

        self.last_sent = time.time() # prevents from sending too rapidly

        self.rcv_queue = [] # stores previous received strings
        self.busy = False # to make thread-safe; indicates if Serial port is currently being used, threads will wait until this is False until doing operations

class Connection(BaseConnection):
    """A more user-friendly interface with the Serial port.

    Not implemented yet
    """
