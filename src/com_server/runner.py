#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Contains implementation of `run` argument from the CLI.
"""

import logging

from . import Connection, RestApiHandler
from .api import Builtins

# logger setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
fmt = logging.Formatter("%(levelname)s [%(asctime)s] - %(message)s")
handler.setFormatter(fmt)

logger.addHandler(handler)

def run(
    baud: int,
    ser_port: list,
    env: str,
    host: str,
    port: str,
    timeout: int,
    send_interval: int,
    queue_size: int,
    logf: str,
    cors: bool,
    has_rr: bool,
    verbose: bool,
) -> None:
    # init connection

    logger.info("Starting up connection with serial port...")
    with Connection(
        baud,
        ser_port[0],
        *ser_port[1:],
        timeout=timeout,
        send_interval=send_interval,
        queue_size=queue_size
    ) as conn:
        logger.info(f"Connection with serial port established at {conn.port}")

        handler = RestApiHandler(conn, add_cors=cors, has_register_recall=has_rr)
        Builtins(handler, verbose=verbose)

        if env == "dev":
            logger.info("Launching Flask app...")
            handler.run_dev(host=host, port=port, logfile=logf)
        else:
            logger.info("Launching Waitress server...")
            handler.run_prod(host=host, port=port, logfile=logf)
