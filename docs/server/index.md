# COM-Server built-in API

The library comes with a built-in API that allows the user to interact in different ways with the serial port. It comes with different versions to avoid breaking changes. Each supported version comes with a prefix in the URL to differentiate the version. Note that the custom endpoints that you add using `RestApiHandler` will not be affected by this.

## Supported versions

Currently, the supported versions are:

- [Version 0](../server/v0) (class name `V0`, all routes prefixed with `/v0`)

## Adding the built-in routes

The simplest way to start a server with all endpoints is to use the CLI. The CLI will add all the routes from all the versions. See the [CLI docs](../guide/cli) for more details.

To add the built-in routes into your program, you need to use the `com_server.api` module. This module provides the built-in routes for all supported versions of the API. For example, to use version 0 of the API, you can simply import the `V0` class from the `com_server.api` module and wrap it around the `RestApiHandler` object. When the server is launched, this will add all routes from version 0, prefixed with `/v0`.

```py
from com_server import Connection, RestApiHandler
from com_server.api import V0

conn = Connection(<baud>, "<port>")
handler = RestApiHandler(conn)
V0(handler) # adds built-in endpoints from version 0

handler.run(host="0.0.0.0", port=8080)
```

All class names and prefixes are listed above, in "supported versions".

To add routes from all versions to the API, import the `Builtins` class from `com_server.api`.

```py
from com_server import Connection, RestApiHandler
from com_server.api import Builtins

conn = Connection(<baud>, "<port>")
handler = RestApiHandler(conn)
Builtins(handler) # adds all built-in endpoints from all versions

handler.run(host="0.0.0.0", port=8080)
```

This will launch a server with routes from all versions with their corresponding URL prefixes, listed above.

Note that adding built-in routes means that those routes cannot be added again later. If they are, it will raise `com_server.EndpointExistsException`.

## Endpoints from RestApiHandler

These endpoints cannot be used in any case with the `RestApiHandler`, even if `has_register_recall` is False. If they are defined again by the user, it will raise `com_server.EndpointExistsException`.

These endpoints will not apply if `has_register_recall` is False, and the response will be a `404 Not Found`.

If an endpoint is reached while another process is using another endpoint, then the endpoint will respond with `503 Service Unavailable`.

```txt
/register
```

Registers an IP to the server. Note that this is IP-based, not
process based, so if there are multiple process on the same computer
connecting to this, the server will not be able to detect it and may
lead to unexpected behavior.

Method: GET

Arguments:
    None

Response:

- `200 OK`: `{"message": "OK"}` if successful
- `400 Bad Request`: 
    - `{"message": "Double registration"}` if this endpoint is reached by an IP while it is registered
    - `{"message": "Not registered; only one connection at a time"}` if this endpoint is reached while another IP is registered
- `503 Service Unavailable`:
    - `{"message": "An endpoint is currently in use by another process."}` if this endpoint was reached while another endpoint is in use.

```txt
/recall
```

Unregisters an IP from a server and allows other IPs to use it.

Method: GET

Arguments:
    None

Response:

- `200 OK`: `{"message": "OK}` if successful
- `400 Bad Request`:
    - `{"message": "Nothing has been registered"}` if try to call without any IP registered
    - `{"message": "Not same user as one in session"}` if called with different IP as the one registered
- `503 Service Unavailable`:
    - `{"message": "An endpoint is currently in use by another process."}` if this endpoint was reached while another endpoint is in use.

## What happens if the serial device disconnects?

When the server is started, there will be a thread checking the connection state of the serial device every 0.01 seconds, and if it disconnects, the thread will attempt to reconnect the device.

Any request made to any endpoint the requires use of the serial port will have a response of `500 Internal Server Error` when the device is disconnected and will behave normally once reconnected.

Notes:

- When it reconnects, it calls the `reconnect()` method in the `Connection` object. It will try to reconnect to the ports given in `__init__()`, which means that if the port was changed somehow between disconnecting and reconnecting, it will not reconnect and will require restarting the server.
- Disconnect and reconnect events will be logged to `stdout` for both development and production servers. You can specify a file to log these events to in the `logfile` parameter when calling [`RestApiHandler.run()`](http://localhost:8000/guide/library-api/#restapihandlerrun_dev) or [`RestApiHandler.run_dev()`](http://localhost:8000/guide/library-api/#restapihandlerrun_prod). The time, logging level (INFO and WARNING), and disconnect and reconnect messages will be logged to the file.
- Disconnecting the serial device will **reset** the receive and send queues.
