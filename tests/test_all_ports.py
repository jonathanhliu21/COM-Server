#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests if lists ports properly
"""

import re

from com_server.disconnect import _get_all_ports
from com_server.tools import all_ports

def test_ports():
    """
    Tests if `all_ports` is listing properly.    
    """

    ports = [a for a, _, _ in all_ports() if re.match("/dev/ttyUSB*", a)]

    assert(len(ports) > 0)

def test_get_all():
    """
    Tests if `_get_all_ports()` is listing properly.
    """

    ports = _get_all_ports()

    ports_all = [a for a in ports if re.match("/dev/ttyUSB*", a)]

    assert(len(ports_all) > 0)
