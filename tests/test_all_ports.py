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
    _usb = glob.glob("/dev/ttyUSB[0-9]*")
    _acm = glob.glob("/dev/ttyACM[0-9]*")
    MATCH = "/dev/ttyUSB[0-9]*|/dev/ttyACM[0-9]*"
elif (sys.platform.startswith("darwin")):
    _usb = glob.glob("/dev/cu.usbserial*")
    _acm = []
    MATCH = "/dev/cu.usbserial.*"
else:
    # platform not supported for the test
    pytestmark = pytest.mark.skip(reason="Test not supported on this platform.")

@pytest.mark.skipif(len(_usb+_acm) <= 0, reason="port not connected")
def test_ports():
    """
    Tests if `all_ports` is listing properly.    
    """

    ports = [a for a, _, _ in all_ports() if re.match(MATCH, a)]

    assert(len(ports) > 0)
