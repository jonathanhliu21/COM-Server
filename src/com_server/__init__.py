#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

# detect platform
if (os.name != "posix" and os.name != "nt"):
    raise EnvironmentError("Platform not supported.")

from .connection import *
from . import *
