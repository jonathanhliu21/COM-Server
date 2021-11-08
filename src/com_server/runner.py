#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Contains implementation of `run` argument from the CLI.
"""

from . import Connection, RestApiHandler, Builtins

def run(baud: int, ser_port: int, env: str, host: str, port: str, timeout: int, send_interval: int):
    # init connection
    conn = Connection(baud, ser_port, timeout=timeout, send_interval=send_interval) 
    handler = RestApiHandler(conn)
    Builtins(handler)

    if (env == "dev"):
        handler.run_dev(host=host, port=port)
    else:
        handler.run_prod(host=host, port=port)
