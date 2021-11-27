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
- Added a changelog to keep track of changes
