#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CLI for COM_Server.

Contains commands to run the COM server.
"""

import logging
import sys

import click
from flask import Flask
from flask import __version__ as f_v
from flask_cors import CORS
from flask_restful import Api
from serial import __version__ as s_v

from . import __version__
from .api import V1
from .connection import Connection
from .server import ConnectionRoutes, start_app

# logger setup
logger = logging.getLogger(__name__)
logger.propagate = (
    False  # prevents from logging twice because waitress calls basicConfig()
)
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
fmt = logging.Formatter("%(levelname)s [%(asctime)s] - %(message)s")
handler.setFormatter(fmt)

logger.addHandler(handler)


def _display_version() -> None:
    _pyth_v = sys.version_info

    p_o = (
        f"COM_Server version: {__version__}\n"
        f"Flask version: {f_v}\n"
        f"Pyserial version: {s_v}\n"
        f"Python version: {_pyth_v.major}.{_pyth_v.minor}.{_pyth_v.micro}"
    )

    click.echo(p_o)
    sys.exit()


@click.group(invoke_without_command=True)
@click.pass_context
@click.option("--version", is_flag=True, help="Print version of COM-Server")
def main(ctx: click.Context, version: bool) -> None:
    """Simple command line tool for COM-Server"""

    if ctx.invoked_subcommand:
        return

    if version:
        _display_version()
    else:
        ctx = click.get_current_context()
        click.echo(ctx.get_help())


@main.command()
@click.argument("baud", type=int)
@click.argument("serport", type=str, nargs=-1)
@click.option(
    "--host",
    type=str,
    default="0.0.0.0",
    help="The name of the host server[default: 0.0.0.0].",
)
@click.option(
    "--port",
    type=int,
    default=8080,
    help="The port of the host server (optional) [default: 8080].",
)
@click.option(
    "--send-int",
    type=int,
    default=1,
    help="How long, in seconds, the program should wait between sending to serial port (aka the send interval) [default: 1].",
)
@click.option(
    "--timeout",
    type=int,
    default=1,
    help="How long, in seconds, the program should wait before exiting when performing time-consuming tasks (aka the timeout) [default: 1].",
)
@click.option(
    "--queue-size",
    type=int,
    default=256,
    help="The maximum size of the receive queue [default: 256].",
)
@click.option(
    "--logfile",
    type=str,
    help="Path to file to log disconnect and reconnect events to.",
)
@click.option(
    "--cors",
    is_flag=True,
    help="If set, then the program will add cross origin resource sharing to all routes.",
)
def run(
    baud: int,
    serport: str,
    host: str,
    port: int,
    send_int: int,
    timeout: int,
    queue_size: int,
    logfile: str,
    cors: bool,
) -> None:
    """
    Launches waitress server with builtin API

    Given baud rate and list of ports, the program will try to connect to
    each one in the order given until a connection works. Then, the
    program will start a web API with routes to interact with the port.

    The prefix to the routes will be /v1/ (e.g. localhost:8080/v1/...)

    Example usage:

    com_server 115200 /dev/ttyUSB0 /dev/ttyUSB1

    This will start a serial connection with baud rate 115200, and the
    program will first try to connect to /dev/ttyUSB0. If that fails,
    it will try to connect to /dev/ttyUSB1, and if both fail, there
    will be an error.
    """

    # start connection and server

    logger.info("Starting up connection with serial port...")
    with Connection(
        baud,
        serport[0],
        *serport[1:],
        timeout=timeout,
        send_interval=send_int,
        queue_size=queue_size,
    ) as conn:
        logger.info(f"Connection with serial port established at {conn.port}")

        app = Flask(__name__)
        api = Api(app, catch_all_404s=True)

        if cors:
            CORS(app)

        handler = ConnectionRoutes(conn)
        V1(handler)

        start_app(app, api, handler, logfile=logfile, host=host, port=port)

    logger.info("exited")
