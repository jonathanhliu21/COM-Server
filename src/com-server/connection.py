#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""

"""

import time
import typing as t

import serial

class Connection:
    """
    """

    def __init__(self, baud: int, port: str, *args, timeout: float = 1, send_freq: t.Union[int, None] = None, queue_size: int = 256, **kwargs) -> None:
        """Initializes the Connection class. 

        `baud`, `port`, `timeout`, and `kwargs` will be passed to pyserial.  

        Parameters:
            - `baud` (int): The baud rate of the Serial connection 
            - `port` (str): The serial port
            - `timeout` (float) (optional): How long the program should wait, in seconds, for Serial data before exiting. By default 1.
            - `send_freq` (int) (optional): Limits the number of sends that occur per minute. Leave as None if you want no limitations. By default None.
            - `queue_size` (int) (optional): The number of previous receives that the program should keep. Must be nonnegative and less than or equal to 8192.
            - `kwargs`: Will be passed to pyserial
        
        Returns: nothing
        """

        # assertions
        assert (queue_size >= 0 and queue_size <= 8192)

        # from above
        self.baud = int(baud)
        self.port = str(port)
        self.timeout = float(timeout)
        self.queue_size = int(queue_size)
        self.send_freq = int(send_freq)

        # initialize Serial object
        self.conn = serial.Serial(port=self.port, baudrate=self.baud, timeout=self.timeout, **kwargs)

        # other
        self.last_sent = time.time() # prevents from sending too rapidly

    def __repr__(self) -> str:
        """
        Returns string representation of self
        """

        return f"Connection<id=0x{hex(id(self))}, " \
            f"{{port={self.port}, baud={self.baud}, timeout={self.timeout}, queue_size={self.queue_size}}}"
