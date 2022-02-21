# /usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Builtin API versioning.

To only add endpoints for a specific version, you can use

```py
from com_server.api import <VERSION>
```

Current supported versions (routes are in parenthesis) are:
- `V0`
- `V1`

For versions >= V1, multiple versions can be used
to wrap a `ConnectionRoutes` object to add endpoints
of multiple versions.
"""

from .v0 import Builtins as V0
from .v1 import V1
