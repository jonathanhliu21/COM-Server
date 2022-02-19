#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

# detect platform
if os.name != "posix" and os.name != "nt":
    raise EnvironmentError("Platform not supported")

# detect version of python
vers = sys.version_info
if vers.major < 3 or (vers.major == 3 and vers.minor < 6):
    raise EnvironmentError("Python version >= 3.6 is required")

from .api_server import ConnectionResource, EndpointExistsException, RestApiHandler
from .base_connection import ConnectException
from .connection import Connection
from .constants import *
from .tools import ReceiveQueue, SendQueue, all_ports

__version__ = "0.2b0"
