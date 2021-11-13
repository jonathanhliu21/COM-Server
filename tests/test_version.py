#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
from com_server import __version__
from pkg_resources import get_distribution

from cmp_version import Version


def test_version():
    """Tests if __version__ and version in setup.cfg matches"""
    
    pkg = get_distribution("com_server")

    assert pkg.version == __version__

def test_version_class_working() -> None:
    """Tests if Version class is working"""

    # test X.Y evaluates to X.Y.0
    assert repr(Version("5.5")) == "5.5.0"

    # Tests Version("0.0a") and Version("0.0b") and ("0.0.") raise exceptions
    with pytest.raises(ValueError):
        Version("0.0a")
    with pytest.raises(ValueError):
        Version("0.0b")
    with pytest.raises(ValueError):
        Version("0.0.")
    with pytest.raises(ValueError):
        Version(".0.0")
    with pytest.raises(ValueError):
        Version("a0.0")

    # test major version compare
    assert Version("1.0.0") < Version("5.0a0")
    assert Version("5.0a0") > Version("1.0.0")
    # test minor version compare
    assert Version("0.3.0") < Version("0.5a0")
    assert Version("0.5a0") > Version("0.3.0")
    # test release type compare
    assert Version("0.0a0") < Version("0.0")
    assert Version("0.0") > Version("0.0a0")
    assert Version("0.1a0") < Version("0.1b0")
    # test release num compare
    assert Version("0.0a0") < Version("0.0a1")
    assert Version("0.0a1") > Version("0.0a0")

    # test eq compare
    assert Version("0.0.0") == Version("0.0.0")
    assert Version("1.0a0") == Version("1.0a0")

if (__name__ == "__main__"):
    v = Version("0.0bbb0")
    print(v)