#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pkg_resources import get_distribution

from com_server import __version__

def test_version():
    """Tests if __version__ and version in setup.cfg matches"""
    
    pkg = get_distribution("com_server")

    assert pkg.version == __version__

if (__name__ == "__main__"):
    test_version()
