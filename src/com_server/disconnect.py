# /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Contains disconnect handling for the `RestApiHandler`
"""

import logging
import threading
import time
import typing as t

from . import connection  # for typing


class Reconnector(threading.Thread):
    """
    Object that detects whenever a connection is disconnected and reconnects
    """

    def __init__(
        self,
        conn: connection.Connection,
        logger: logging.Logger,
        logfile: t.Optional[str] = None,
    ) -> None:
        """Constructor

        Takes in the connection object to watch and reconnect if it is disconnected.
        This is NOT thread safe and not meant to be used outside of the `RestApiHandler`.
        It is recommended to implement your own disconnect/reconnect handler.

        Arguments:
        - `conn` (Connection): connection to watch and reconnect to.
        - `prod` (bool): indicates if this is a production server
        - `logfile` (str, None): the path to the file to log disconnects to
        """

        self._conn = conn
        self._logf = logfile

        self._logger = logger
        self._logger.propagate = (
            False  # prevents from logging twice because waitress calls basicConfig()
        )
        self._logger.setLevel(logging.INFO)
        self._init_logger()

        if self._logf:
            self._init_logger_file()

        # threading
        super().__init__(daemon=True)

    def run(self) -> None:
        """What to run in thread

        In this case, checks if the serial port every 0.01 seconds.
        """

        while True:
            if not self._conn.connected:
                self._logger.warning("Device disconnected")
                self._logger.info("Attempting to reconnect...")

                self._conn.reconnect()

                self._logger.info(f"Device reconnected at {self._conn.port}")

            time.sleep(0.01)

    def _init_logger(self) -> None:
        """Initializes logger to stdout"""

        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)

        fmt = logging.Formatter("%(levelname)s [%(asctime)s] - %(message)s")
        handler.setFormatter(fmt)

        self._logger.addHandler(handler)

    def _init_logger_file(self) -> None:
        """Initializes logger to file"""

        handler = logging.FileHandler(self._logf)
        handler.setLevel(logging.INFO)

        fmt = logging.Formatter("%(levelname)s [%(asctime)s] - %(message)s")
        handler.setFormatter(fmt)

        self._logger.addHandler(handler)
