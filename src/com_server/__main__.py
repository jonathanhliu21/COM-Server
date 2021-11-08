#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CLI for COM_Server.

Contains commands to run the COM server.
"""

import sys

from docopt import docopt

from . import __version__, runner

PARSE = """COM_Server command line tool

A simple command line tool to start the API server that interacts
with the serial port in an development environment or a 
production environment.

Usage:
    com_server (-p | --serport) <serport> (-b | --baud) <baud> run [--env=<env>] [--host=<host>] [--port=<port>] [--s-int=<s-int>] [--to=<to>]
    com_server -h | --help
    com_server --version

Options:
    -p, --serport    The serial port to connect to.
    -b, --baud       The baud rate of the serial connection.
    --env=<env>      Development or production environment. Value must be 'dev' or 'prod'. [default: dev].
    --host=<host>    The name of the host server (optional) [default: 0.0.0.0].
    --port=<port>    The port of the host server (optional) [default: 8080].
    --s-int=<s-int>  How long, in seconds, the program should wait between sending to serial port [default: 1].
    --to=<to>        How long, in seconds, the program should wait before exiting when performing time-consuming tasks [default: 1].

    -h, --help      Show help.
    --version       Show version.
"""

def _display_version() -> None:
    print(f"COM_Server version: {__version__}")
    sys.exit()

def main() -> None:
    args = docopt(PARSE)

    if (args["--version"]):
        # if asking for version
        _display_version()
    
    if (args["run"]):
        # if asking to run

        baud = args["<baud>"]
        serport = args["<serport>"]
        env = args["--env"]
        host = args["--host"]
        port = args["--port"]
        timeout = args["--to"]
        send_interval = args["--s-int"]

        if (env not in ('dev', 'prod')):
            print("Value of <env> must be \"dev\" or \"prod\".")
            sys.exit(1)
        
        runner.run(baud, serport, env, host, port, timeout, send_interval)

        print("Exited")
