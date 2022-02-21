#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script to run tests that need a serial connection to run
"""

import os
import pytest
import sys

pytest.main([os.path.join("tests", "active")] + sys.argv[1:])
