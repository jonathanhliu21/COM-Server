#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Version testing

Don't want to run when running `pytest`, only run when something
is pushed to develop branch or PR to master.
"""

import configparser
import requests
from com_server import __version__

from passive.cmp_version import Version


def test_version_greater() -> None:
    """Tests if current version is greater than version on master branch on github"""

    req = requests.get(
        "https://raw.githubusercontent.com/jonyboi396825/COM-Server/master/setup.cfg"
    )
    cfg = configparser.ConfigParser()
    cfg.read_string(req.text)

    master_vers = Version(cfg["metadata"]["version"])
    cur_vers = Version(__version__)

    assert cur_vers > master_vers
