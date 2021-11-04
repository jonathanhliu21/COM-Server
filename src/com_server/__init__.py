#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

# detect platform
if (os.name != "posix" and os.name != "nt"):
    raise EnvironmentError("Platform not supported.")

from .api_server import ConnectionResource, RestApiHandler
from .base_connection import BaseConnection
from .connection import Connection
from .tools import all_ports
