#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script to run tests that need a serial connection to run
"""

import os
import pytest
import requests
import sys

try:
    requests.get("http://127.0.0.1:8080")
except requests.exceptions.ConnectionError:
    print("Server not found. Skipping tests and exiting.")
    sys.exit()

def main() -> None:
    pytest.main([os.path.join("tests", "active")] + sys.argv[1:])

if __name__ == "__main__":
    main()
