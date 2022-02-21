#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests if lists ports properly. Needs Arduino microcontroller to be plugged in to test (otherwise skipped).
"""

import glob
import sys
import re

from com_server.tools import all_ports

import pytest

if (sys.platform.startswith("linux")):
    # usb and acm for linux only
    _usb = glob.glob("/dev/ttyUSB[0-9]*")
    _acm = glob.glob("/dev/ttyACM[0-9]*")
    MATCH = "/dev/ttyUSB[0-9]*|/dev/ttyACM[0-9]*"
elif (sys.platform.startswith("darwin")):
    # mac; use cu.*, not tty.*
    _usb = glob.glob("/dev/cu.usbserial*")
    _acm = glob.glob("/dev/cu.usbmodem*")
    MATCH = "/dev/cu.usb(serial|modem).*"
elif (sys.platform.startswith("win")):
    # windows
    _usb = [f"COM{i+1}" for i in range(256)]
    _acm = []
    MATCH= "COM[0-9]+"
else:
    # platform not supported for the test
    _usb, _acm = [], []

@pytest.mark.skipif(len(_usb+_acm) <= 0, reason="port not connected")
def test_ports():
    """
    Tests if `all_ports` is listing properly.    
    """

    ports = [a for a, _, _ in all_ports() if re.match(MATCH, a)]

    assert(len(ports) > 0)
