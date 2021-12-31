# /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Builtin API versioning.

To only add endpoints for a specific version, you can use

```py
from com_server.api import <VERSION>
```

Current supported versions (routes are in parenthesis) are:
- `V0` (`/v0/*`)

To use all versions, import `Builtins`:

```py
from com_server.api import Builtins
```

Each version will be prefixed by their own route (see list above).
"""

from .. import RestApiHandler
from .v0 import Builtins as V0


class Builtins:
    def __init__(self, handler: RestApiHandler, *args: tuple, **kwargs: dict) -> None:
        """
        Adds builtin endpoints for all versions.

        Parameters:

        - `handler`: The `RestApiHandler` class that this class should wrap around

        Other parameters will be passed to the different versions.
        """

        V0(handler, *args, **kwargs) 
