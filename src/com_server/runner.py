#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Contains implementation of `run` argument from the CLI.
"""

from . import Connection, RestApiHandler
from .api import Builtins


def run(
    baud: int,
    ser_port: list,
    env: str,
    host: str,
    port: str,
    timeout: int,
    send_interval: int,
    queue_size: int,
    cors: bool,
    has_rr: bool,
    verbose: bool,
) -> None:
    # init connection

    print("Starting up connection with serial port...")
    with Connection(
        baud,
        ser_port[0],
        *ser_port[1:],
        timeout=timeout,
        send_interval=send_interval,
        queue_size=queue_size
    ) as conn:
        print("Connection with serial port established at", conn.port)

        handler = RestApiHandler(conn, add_cors=cors, has_register_recall=has_rr)
        Builtins(handler, verbose=verbose)

        if env == "dev":
            print("Launching Flask app...")
            handler.run_dev(host=host, port=port)
        else:
            print("Launching Waitress server...")
            handler.run_prod(host=host, port=port)
