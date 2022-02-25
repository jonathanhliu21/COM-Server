# COM-Server library API reference

## com_server.Connection

### BaseConnection

**Below are members of `Connection` inherited from `BaseConnection`.**

::: com_server.base_connection.BaseConnection
    handler: python
    selection:
        members:
            - __init__
            - connect
            - disconnect
            - send
            - receive
            - connected
            - timeout
            - send_interval
            - conn_obj
            - available
            - port
    rendering:
        show_source: false
        heading_level: 3

### Connection

**Below are members of `Connection` not inherited from `BaseConnection`.**

::: com_server.Connection
    handler: python
    selection:
        members:
            - all_rcv
            - conv_bytes_to_str
            - custom_io_thread
            - get
            - get_first_response
            - receive_str
            - reconnect
            - send_for_response
            - wait_for_response
    rendering:
        show_source: false
        heading_level: 3

## com_server.ConnectionRoutes

::: com_server.ConnectionRoutes
    handler: python
    selection:
        members:
            - __init__
            - add_resource 
    rendering:
        show_source: false
        heading_level: 3

## com_server.start_app

::: com_server.start_app
    handler: python
    rendering:
        show_source: false
        heading_level: 3
        show_root_heading: true

## com_server.add_resources

::: com_server.add_resources
    handler: python
    rendering:
        show_source: false
        heading_level: 3
        show_root_heading: true

## com_server.start_conns

::: com_server.start_conns
    handler: python
    rendering:
        show_source: false
        heading_level: 3
        show_root_heading: true

## com_server.disconnect_conns

::: com_server.disconnect_conns
    handler: python
    rendering:
        show_source: false
        heading_level: 3
        show_root_heading: true

## com_server.all_ports

::: com_server.all_ports
    handler: python
    rendering:
        show_source: false
        heading_level: 3
        show_root_heading: true

## com_server.api

This is the server API module for the built-in endpoints of COM-Server.

See the [Server API](../../server).


## com_server.SendQueue

::: com_server.SendQueue
    handler: python
    selection:
        members:
        - __init__
        - copy
        - deepcopy
        - front
        - pop
    rendering:
        show_source: false
        heading_level: 3

## com_server.ReceiveQueue

::: com_server.ReceiveQueue
    handler: python
    selection:
        members:
        - __init__
        - copy
        - deepcopy
        - pushitems
    rendering:
        show_source: false
        heading_level: 3

---

## Constants

```py
NO_TIMEOUT = float("inf")
```

Use this if you do not want a timeout. Not recommended.

```py
NO_SEND_INTERVAL = 0
```

Use this if you do not want a send interval. Not recommended.

```py
NORMAL_BAUD_RATE = 9600
FAST_BAUD_RATE = 115200
```

Standard baud rates that are commonly used.

```py
NO_RCV_QUEUE = 1 
RCV_QUEUE_SIZE_XSMALL = 32
RCV_QUEUE_SIZE_SMALL = 128
RCV_QUEUE_SIZE_NORMAL = 256
RCV_QUEUE_SIZE_LARGE = 512
RCV_QUEUE_SIZE_XLARGE = 1024
```

Different receive queue sizes for `queue_size`. Default is `RCV_QUEUE_SIZE_NORMAL`.

```py
DEFAULT_HOST="0.0.0.0"
DEFAULT_PORT=8080
```

Default host and port for the server.

---

## Exceptions

### com_server.ConnectException  

This exception is raised whenever a user tries to do an operation with the `Connection` class while it is disconnected, but the operation requires it to be connected, or vice versa.

### com_server.EndpointExistsException

This exception is raised if the user tries to add a route to the `RestApiHandler` that already exists.

### com_server.DuplicatePortException

Raised when trying to start a server with two or more `ConnectionRoutes` objects (**experimental**) and any of them share a common serial port. This is needed to prevent confusion when reconnecting to the ports.

---

## Old Classes

Use of these is not recommended because these will be deprecated soon.

### com_server.RestApiHandler

**NOTE: This will not be supported for versions >=0.2. Use `ConnectionRoutes` instead.**

A handler for creating endpoints with the `Connection` and `Connection`-based objects.

This class provides the framework for adding custom endpoints for doing
custom things with the serial connection and running the local server
that will host the API. It uses a `flask_restful` object as its back end. 

Note that endpoints cannot have the names `/register` or `/recall`.
Additionally, resource classes have to extend the custom `ConnectionResource` class
from this library, not the `Resource` from `flask_restful`.

`500 Internal Server Error`s will occur with endpoints dealing with the connection
if the serial port is disconnected. The server will spawn another thread that will
immediately try to reconnect the serial port if it is disconnected. However, note
that the receive and send queues will **reset** when the serial port is disconnected.

If another process accesses an endpoint while another is
currently being used, then it will respond with
`503 Service Unavailable`.

More information on [Flask](https://flask.palletsprojects.com/en/2.0.x/) and 
[flask-restful](https://flask-restful.readthedocs.io/en/latest/)

Register and recall endpoints:

- `/register` (GET): An endpoint to register an IP; other endpoints will result in `400` status code
if they are accessed without accessing this first (unless `has_register_recall` is False); 
if an IP is already registered then this will result in `400`; IPs must call this first before 
accessing serial port (unless `has_register_recall` is False) 
- `/recall` (GET): After registered, can call `/recall` to "free" IP from server, allowing other IPs to 
call `/register` to use the serial port

#### RestApiHandler.\_\_init\_\_()

```py
def __init__(conn, has_register_recall=True, add_cors=False, catch_all_404s=True, **kwargs)
```

Constructor for class

Parameters:

- `conn` (`Connection`): The `Connection` object the API is going to be associated with. 
- `has_register_recall` (bool): If False, removes the `/register` and `/recall` endpoints
so the user will not have to use them in order to access the other endpoints of the API.
That is, visiting endpoints will not respond with a 400 status code even if `/register` was not
accessed. By default True. 
- `add_cors` (bool): If True, then the Flask app will have [cross origin resource sharing](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS) enabled. By default False.
- `catch_all_404s` (bool): If True, then there will be JSON response for 404 errors. Otherwise, there will be a normal HTML response on 404. By default True.
- `**kwargs`, will be passed to `flask_restful.Api()`. See [here](https://flask-restful.readthedocs.io/en/latest/api.html#id1) for more info.

#### RestApiHandler.add_endpoint()

```py
def add_endpoint(endpoint)
```

Decorator that adds an endpoint

This decorator should go above a class that
extends `ConnectionResource`. The class should
contain implementations of request methods such as
`get()`, `post()`, etc. similar to the `Resource`
class from `flask_restful`. To use the connection
object, use the `self.conn` attribute of the class
under the decorator.

For more information, see the `flask_restful` [documentation](https://flask-restful.readthedocs.io).

Note that duplicate endpoints will result in an exception.
If there are two classes of the same name, even in different
endpoints, the program will append underscores to the name
until there are no more repeats. For example, if one class is
named "Hello" and another class is also named "Hello", 
then the second class name will be changed to "Hello_". 
This happens because `flask_restful` interprets duplicate class 
names as duplicate endpoints.

If another process accesses an endpoint while another is
currently being used, then it will respond with
`503 Service Unavailable`.

Parameters:

- `endpoint`: The endpoint to the resource. Cannot repeat.
`/register` and `/recall` cannot be used, even if
`has_register_recall` is False

#### RestApiHandler.add_resource()

```py
def add_resource(*args, **kwargs)
```

Calls `flask_restful.add_resource`. 

Allows adding endpoints that do not interact with the serial port.

See [here](https://flask-restful.readthedocs.io/en/latest/api.html#flask_restful.Api.add_resource)
for more info on `add_resource` and [here](https://flask-restful.readthedocs.io)
for more info on `flask_restful` in general. 

#### RestApiHandler.run()

```py
def run(**kwargs)
```

Launches the Flask app as a Waitress production server (recommended).

Parameters:

- `logfile` (str, None): The path of the file to log serial disconnect and reconnect events to.
Leave as None if you do not want to log to a file. By default None.

All arguments in `**kwargs` will be passed to `waitress.serve()`.
For more information, see [here](https://docs.pylonsproject.org/projects/waitress/en/stable/arguments.html#arguments).
For Waitress documentation, see [here](https://docs.pylonsproject.org/projects/waitress/en/stable/).

If nothing is included, then runs on `http://0.0.0.0:8080`

Automatically disconnects the `Connection` object after
the server is closed.

#### RestApiHandler.run_dev()

```py
def run_dev(**kwargs)
```

Launches the Flask app as a development server.

Not recommended because this is slower, and development features
such as debug mode and restarting do not work most of the time.
Use `run()` instead.

Parameters:

- `logfile` (str, None): The path of the file to log serial disconnect and reconnect events to.
Leave as None if you do not want to log to a file. By default None.

All arguments in `**kwargs` will be passed to `Flask.run()`.
For more information, see [here](https://flask.palletsprojects.com/en/2.0.x/api/#flask.Flask.run).
For documentation on Flask in general, see [here](https://flask.palletsprojects.com/en/2.0.x/).

Automatically disconnects the `Connection` object after
the server is closed.

Some arguments include: 

- `host`: The host of the server. Ex: `localhost`, `0.0.0.0`, `127.0.0.1`, etc.
- `port`: The port to host it on. Ex: `5000` (default), `8000`, `8080`, etc.
- `debug`: If the app should be used in debug mode. Very unreliable and most likely will not work.

#### RestApiHandler.run_prod()

```py
def run_prod(**kwargs)
```

Same as `run()` but here for backward compatibility.

#### RestApiHandler.flask_obj

Getter:  

- Gets the `Flask` object that is the backend of the endpoints and the server.

This can be used to modify and customize the `Flask` object in this class.

#### RestApiHandler.api_obj

Getter:  

- Gets the `flask_restful` API object that handles parsing the classes.

This can be used to modify and customize the `Api` object in this class.
