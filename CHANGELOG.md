# 0.1 Development Release 1

Previous version: 0.0.*

## Changes from previous version:

- Added the `SendQueue` and `ReceiveQueue` objects which allow the user to use  the send queues and receive queues without accidentally breaking the program
    - Added tests for these objects
- Added the ability for the user to define a custom IO thread with a connection object, the `ReceiveQueue`, and the `SendQueue` 
- Added constants for the common baud rates:
    - `NORMAL_BAUD_RATE`: 9600 bits/sec
    - `FAST_BAUD_RATE`: 115200 bits/sec
- Added the ability to initialize with multiple ports, addressing [#39](https://github.com/jonyboi396825/COM-Server/issues/39)
- Added a changelog to keep track of changes
