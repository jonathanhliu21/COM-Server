# /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This file contains the implementation to the HTTP server that serves
the web API for the Serial port.
"""

import typing as t

import flask
import flask_restful

from . import base_connection, connection # for typing
