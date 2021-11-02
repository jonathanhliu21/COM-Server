#/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This file contains the implementation to the HTTP server that serves
the web API for the Serial port.
"""

import typing as t

from flask import Flask
from flask_restful import Resource, Api, reqparse

from . import connection


class EndpointExistsException(Exception):
    pass

class UninitializedException(Exception):
    pass

class Rest_Connection():
    """
    """