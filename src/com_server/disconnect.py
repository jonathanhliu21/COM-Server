# /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Contains disconnect handling for the `RestApiHandler`
"""

import threading
import time

from . import connection  # for typing

class Reconnector(threading.Thread):
    """
    Object that detects whenever a connection is disconnected and reconnects
    """

    def __init__(self, conn: connection.Connection, v: bool) -> None:
        """Constructor

        Takes in the connection object to watch and reconnect if it is disconnected.
        This is NOT thread safe and not meant to be used outside of the `RestApiHandler`.
        It is recommended to implement your own disconnect/reconnect handler.

        Arguments:
        - `conn` (Connection): connection to watch and reconnect to.
        - `v` (bool): verbose; if the program should print when the serial device disconnects
        """

        self._conn = conn
        self._v = v

        super().__init__(daemon=True)
    
    def run(self) -> None:
        """What to run in thread        

        In this case, checks if the serial port every 0.01 seconds.
        """

        while True:
            if not self._conn.connected:
                if self._v:
                    print("Device disconnected")

                self._conn.reconnect()

                if self._v:
                    print("Device reconnected")

            time.sleep(0.01)
    