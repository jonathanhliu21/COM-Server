# /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Contains disconnect handling for the `RestApiHandler`
"""

import logging
import threading
import time
import typing as t

from .connection import Connection


class BaseReconnector(threading.Thread):
    """Base reconnector class"""

    _logger: logging.Logger
    _logf: t.Optional[str]

    def _init_logger(self) -> None:
        """Initializes logger to stdout"""

        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)

        fmt = logging.Formatter("%(levelname)s [%(asctime)s] - %(message)s")
        handler.setFormatter(fmt)

        self._logger.addHandler(handler)

    def _init_logger_file(self) -> None:
        """Initializes logger to file"""

        assert self._logf is not None, "No logfile provided"  # mypy

        handler = logging.FileHandler(self._logf)
        handler.setLevel(logging.INFO)

        fmt = logging.Formatter("%(levelname)s [%(asctime)s] - %(message)s")
        handler.setFormatter(fmt)

        self._logger.addHandler(handler)


class Reconnector(BaseReconnector):
    """
    Object that detects whenever a single connection is disconnected and reconnects
    """

    def __init__(
        self,
        conn: Connection,
        logger: logging.Logger,
        logfile: t.Optional[str] = None,
    ) -> None:
        """Constructor

        Takes in the connection object to watch and reconnect if it is disconnected.
        This is NOT thread safe and not meant to be used outside of the `RestApiHandler`.
        It is recommended to implement your own disconnect/reconnect handler.

        Arguments:
        - `conn` (Connection): connection to watch and reconnect to.
        - `logger` (Logger): logger object
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


class MultiReconnector(BaseReconnector):
    """
    Object that detects whenever any given connection is disconnected and reconnects
    """

    def __init__(
        self,
        logger: logging.Logger,
        *conns: Connection,
        logfile: t.Optional[str] = None,
    ) -> None:
        """
        Takes in the connection objects to watch and reconnect if any are disconnected.
        This is NOT thread safe and not meant to be used outside of other connection objects.
        You should implement your own disconnect/reconnect handler.

        Arguments:
        - `logger` (Logger): logger object
        - `*conns` (Connection): connections to watch and reconnect to.
        - `logfile` (str, None): the path to the file to log disconnects to
        """

        self._conns = conns
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

        cur_reconn = set()

        def _reconn(conn: Connection) -> None:
            """
            reconnect thread
            """

            if conn in cur_reconn:
                # if currently reconnecting, then exit
                return

            cur_reconn.add(conn)

            self._logger.warning(f"Device at {conn.port} disconnected")
            self._logger.info("Attempting to reconnect...")

            conn.reconnect()

            self._logger.info(f"Device reconnected at {conn.port}")

            # remove of set of currently reconnecting objects after reconnected
            cur_reconn.remove(conn)

        while True:
            for conn in self._conns:
                if conn in cur_reconn:
                    continue

                if not conn.connected:
                    # start thread to reconnect
                    threading.Thread(target=_reconn, args=(conn,), daemon=True).start()

            time.sleep(0.01)
