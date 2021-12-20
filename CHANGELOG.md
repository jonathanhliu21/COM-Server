# 0.1 Beta Release 1

Previous version: 0.1b0

## IMPORTANT: BREAKING changes from previous version:

- Updated CLI - see [CLI docs](https://com-server.readthedocs.io/en/latest/guide/cli/) to view how the CLI now works. Previous commands may not work.
- Updated `reconnect()` method; reconnects using ports provided in `__init__()` method rather than providing a port.

## Changes from previous version:

- Fixed [#63](https://github.com/jonyboi396825/COM-Server/issues/63) by making 404 handling default behavior
- Made IO thread in `BaseConnection` abstract
- Added new endpoint `/connection_state`, getting some properties of the `Connection` object, addressing [#60](https://github.com/jonyboi396825/COM-Server/issues/60)
- Added option to remove 0.01 second delay at end of IO thread, addressing [#68](https://github.com/jonyboi396825/COM-Server/issues/68)
- `exception` in `BaseConnection` and `Connection` objects is now **DEPRECATED**

# 0.1 Beta Release 0

Previous version: 0.0.*

## IMPORTANT: BREAKING changes from previous version:

- Changed the way the `RestApiHandler.add_endpoint` decorator works:
    - Instead of having the decorator above a function which returns a nested class, the decorator will instead go directly above the class that extends `ConnectionResource`. To use the connection, use `self.conn` in the methods.

## Changes from previous version:

- Added the `SendQueue` and `ReceiveQueue` objects which allow the user to use  the send queues and receive queues without accidentally breaking the program
    - Added tests for these objects
- Added the ability for the user to define a custom IO thread with a connection object, the `ReceiveQueue`, and the `SendQueue` 
- Added constants for the common baud rates:
    - `NORMAL_BAUD_RATE`: 9600 bits/sec
    - `FAST_BAUD_RATE`: 115200 bits/sec
- Added the ability to initialize with multiple ports, addressing [#39](https://github.com/jonyboi396825/COM-Server/issues/39)
- Added the ability to add [cross origin resource sharing](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS) to the Flask object in the `RestApiHandler`
- Added verbose mode where the program will print arguments received from request to `stdout`
- Formatted code using [black](https://black.readthedocs.io/en/stable/index.html)
- Added more tests that actually test that the data is being sent and received correctly, addressing [#34](https://github.com/jonyboi396825/COM-Server/issues/34)
- Added a changelog to keep track of changes
