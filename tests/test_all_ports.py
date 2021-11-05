#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests if lists ports properly. Needs Arduino microcontroller to be plugged in to test (otherwise skipped).
"""

import glob
import sys
import re

from com_server.disconnect import _get_all_ports
from com_server.tools import all_ports

import pytest

_usb = glob.glob("/dev/ttyUSB[0-9]*")
_acm = glob.glob("/dev/ttyACM[0-9]*")

@pytest.mark.skipif(not sys.platform.startswith("linux"), len(_usb+_acm) <= 0, reason="port not connected")
def test_ports():
    """
    Tests if `all_ports` is listing properly.    
    """

    ports = [a for a, _, _ in all_ports() if re.match("/dev/ttyUSB*", a)]

    assert(len(ports) > 0)

@pytest.mark.skipif(not sys.platform.startswith("linux"), len(_usb+_acm) <= 0, reason="port not connected")
def test_get_all():
    """
    Tests if `_get_all_ports()` is listing properly.
    """

    ports = _get_all_ports()

    ports_all = [a for a in ports if re.match("/dev/ttyUSB*", a)]

    assert(len(ports_all) > 0)
