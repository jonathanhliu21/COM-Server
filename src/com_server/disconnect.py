# /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Checks for disconnect of Serial port.
"""

import os
import signal
import threading
import time
import typing as t

from .tools import all_ports


def _get_all_ports() -> list:
    """Returns a list of serial ports.
    """

    return [a for a, _, _ in all_ports()]


def _disc_thread(obj: t.Any, exit_on_fail: bool) -> None:
    """Thread for handling disconnects
    """

    while (True):
        p = _get_all_ports()

        if (obj.connected and obj.port not in p):
            # disconnect object if connected
            obj.disconnect()

            # if exit, then kill main thread with SIGTERM
            if (exit_on_fail):
                os.kill(os.getpid(), signal.SIGTERM)

        time.sleep(2)


def disconnect_handler(obj: t.Any, exit_on_fail: bool) -> None:
    """A disconnect handler that handles disconnecting a `Connection` object.

    Given `Connection` object (an instance of `BaseConnection`), 
    detects if its port is in list of serial ports every 2 seconds.
    If not, then calls its `disconnect` method and safely disconnects it.

    Parameters:
    - `obj`: The `Connection` (an instance of `BaseConnection`) object
    - `exit_on_fail`: If True, then exits main program upon disconnect. Does NOT work on Windows.
    """

    # detect Windows for disconnect, as interrupting main thread is not supported
    if (os.name == "nt"):
        if (exit_on_fail):
            raise EnvironmentError("exit_on_fail is not supported on Windows")

    threading.Thread(name="disconnect-detection-thread", target=_disc_thread, daemon=True, args=(
        obj, exit_on_fail)).start()  # start thread
