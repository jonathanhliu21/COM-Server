#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script to run tests from V0 API and RestApiHandler
"""

import os
import pytest
import sys

def main() -> int:
    return pytest.main([os.path.join("tests", "old")] + sys.argv[1:])

if __name__ == "__main__":
    sys.exit(main())
