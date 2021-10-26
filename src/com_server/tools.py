#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Provides a set of functions that could be generally useful.
"""

import typing as t

import serial
import serial.tools.list_ports

def all_ports() -> t.Generator:
    """Gets all ports from serial interface.

    Gets ports from Serial interface by calling `serial.tools.list_ports.comports()`.
    See [here](https://pyserial.readthedocs.io/en/latest/tools.html#module-serial.tools.list_ports) for more info.
    """

    return serial.tools.list_ports.comports()
