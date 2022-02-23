#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script for running tests that do not need a serial connection to run.
"""

import os
import pytest
import sys

def main() -> None:
    pytest.main([os.path.join("tests", "passive")] + sys.argv[1:])

if __name__ == "__main__":
    main()
