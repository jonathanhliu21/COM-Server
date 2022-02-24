# Known issues

A list of known issues with COM-Server.

## Sending/receiving long strings of data

Sending or reading anything longer than 50 characters may lead to partial data readings when using the default IO thread. This is because it takes time to read the data, and if there is too much being sent over a longer period of time, then the program would think that there is less data to be read from the serial buffer than there actually is. To solve this, I added a short delay when reading the data to account for the time that the data takes to be read. This means that sending/receiving large amounts of data may lead to slower IO (because of the way the IO thread is written).

It is recommended that you write your **own** IO thread using `Connection.custom_io_thread()`.

## Multiple `ConnectionRoutes` objects

Starting a server with multiple serial connections is currently untested. If any bugs come up, add a new issue in the [issue tracker](https://github.com/jonyboi396825/COM-Server/issues) so I can list them here and (hopefully) fix them.

## Typing

Although COM-Server _technically_ supports static typing with `mypy`, many of its dependencies (pyserial, waitress, flask_restful, and flask_cors) do not, so you may need to ignore those imports in a `mypy.ini` file.
