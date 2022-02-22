# COM-Server Library API

## Functions

### com_server.all_ports()

```py
def all_ports(**kwargs)
```

Gets all ports from serial interface.

Gets ports from Serial interface by calling `serial.tools.list_ports.comports()`.
See [here](https://pyserial.readthedocs.io/en/latest/tools.html#module-serial.tools.list_ports) for more info.

### com_server.start_app()

```py
def start_app(app, api, *routes, logfile, host, port, cleanup, **kwargs)
```

Starts a waitress production server that serves the Flask app
given `ConnectionRoutes` objects.

Using this is recommended over calling `add_resources()`,
`start_conns()`, `serve_app()`, and `disconnect_conns()`
separately.

All `Connection`s in `routes` have to be connected initially, or an exception will be thrown.

Note that connection objects between `ConnectionRoutes`
can share no ports in common.

**Also note that adding multiple `ConnectionRoutes` is
not tested and may result in very unexpected behavior
when disconnecting and reconnecting**.

Lastly, note that `sys.exit()` will be called in this,
so add any cleanup operations to the `cleanup` parameter.

Parameters:

- `app`: The Flask object that runs the server
- `api`: The `flask_restful` `Api` object that adds the resources
- `*routes`: The `ConnectionRoutes` objects to add to the server
- `logfile`: The path of the file to log serial disconnect and reconnect events to.
Leave as None if you do not want to log to a file. By default None.
- `host`: The host of server (e.g. 0.0.0.0 or 127.0.0.1). By default 0.0.0.0
- `port`: The port to host the server on (e.g. 8080, 8000, 5000). By default 8080.
- `cleanup`: cleanup function to be called after waitress is done serving app. By default None.
- `**kwargs`: will be passed to `waitress.serve()`

Returns:

- nothing

### com_server.add_resources()

```py
def add_resources(api, *routes)
```

Adds all resources given in `servers` to the given `Api`.

This has to be called along with `start_conns()` **before** calling `start_app()` or running a flask app.

Parameters:

- `api`: The `flask_restful` `Api` object that adds the resources
- `routes`: The `ConnectionRoutes` objects to add to the server

Returns:

- nothing


### com_server.start_conns()

```py
def start_conns(logger, *routes, logfile)
```
Initializes serial connections and disconnect handler.

This has to be called along with `add_resources()` **immediately before** calling `start_app()` or running a flask app.

Note that adding multiple routes to `start_conns` is experimental and currently
not being tested, and it probably has multiple issues right now.

Parameters:

- `routes`: The `ConnectionRoutes` objects to initialize connections from
- `logger`: a python logging object
- `logfile`: file to log messages to

Returns:

- nothing

### com_server.disconnect_conns()

```py
def disconnect_conns(*routes)
```

Disconnects all `Connection` objects in provided `ConnectionRoutes` objects

It is recommended to call this after `start_app()` to make sure that the serial
connections are closed.

Note that calling this will exit the program using `sys.exit()`.

Parameters:

- `routes`: The `ConnectionRoutes` objects to disconnect connections from

Returns:

- nothing

---

## Classes

### com_server.Connection

Class that interfaces with the serial port.

**Warning**: Before making this object go out of scope, make sure to call `disconnect()` in order to avoid zombie threads.
If this does not happen, then the IO thread will still be running for an object that has already been deleted.

#### Connection.\_\_init\_\_()

```py
def __init__(baud, port, *ports, exception=True, timeout=1, send_interval=1, queue_size=256, exit_on_disconnect=True, rest_cpu=True, **kwargs)
```

Initializes the Connection class. 

`baud`, `port` (or a port within `ports`), `timeout`, and `kwargs` will be passed to pyserial.  
For more information, see [here](https://pyserial.readthedocs.io/en/latest/pyserial_api.html#serial.Serial).

Parameters:

- `baud` (int): The baud rate of the serial connection 
- `port` (str): The serial port
- `*ports`: Alternative serial ports to choose if the first port does not work. The program will try the serial ports in order of arguments and will use the first one that works.
- `timeout` (float): How long the program should wait, in seconds, for serial data before exiting. By default 1.
- `exception` (bool): (**DEPRECATED**) Raise an exception when there is a user error in the methods rather than just returning. By default True.
- `send_interval` (float): Indicates how much time, in seconds, the program should wait before sending another message. 
Note that this does NOT mean that it will be able to send every `send_interval` seconds. It means that the `send()` method will 
exit if the interval has not reached `send_interval` seconds. NOT recommended to set to small values. By default 1.
- `queue_size` (int): The number of previous data that was received that the program should keep. Must be nonnegative. By default 256.
- `exit_on_disconnect` (bool): If True, sends `SIGTERM` signal to the main thread if the serial port is disconnected. Does NOT work on Windows. By default False.
- `rest_cpu` (bool): If True, will add 0.01 second delay to end of IO thread. Otherwise, removes those delays but will result in increased CPU usage.
Not recommended to set False with the default IO thread. By default True.
- `kwargs`: Will be passed to pyserial.

Returns: nothing

#### Connection.\_\_enter\_\_()

```py
def __enter__()
```

A context manager for the `BaseConnection` object. 

When in a context manager, it will automatically connect itself
to its serial port and returns itself. 

#### Connection.\_\_exit\_\_()

```py
def __exit__(exc_type, exc_value, exc_tb)
```

A context manager for the `BaseConnection` object. 

When exiting from the context manager, it automatically closes itself and exits from the threads it had created.


#### Connection.connect()

```py
def connect()
```

Begins connection to the serial port.

When called, initializes a serial instance if not initialized already. Also starts the IO thread.

Parameters: None

Returns: None

#### Connection.disconnect()

```py
def disconnect()
```

Closes connection to the serial port.

When called, calls `Serial.close()` then makes the connection `None`. 
If it is currently closed then just returns.
Forces the IO thread to close.

**NOTE**: This method should be called if the object will not be used anymore
or before the object goes out of scope, as deleting the object without calling 
this will lead to stray threads.

Parameters: None

Returns: None

#### Connection.send()

```py
def send(*args, check_type=True, ending='\r\n', concatenate=' ')
```

Sends data to the port

If the connection is open and the interval between sending is large enough, 
then concatenates args with a space (or what was given in `concatenate`) in between them, 
encodes to an `utf-8` `bytes` object, adds a carriage return and a newline to the end (i.e. "\\r\\n") (or what was given as `ending`), then sends to the serial port.

Note that the data does not send immediately and instead will be added to a queue. 
The queue size limit is 65536 byte objects. Anything more that is trying to be sent will not be added to the queue.
Sending data too rapidly (e.g. making `send_interval` too small, varies from computer to computer) is not recommended,
as the queue will get too large and the send data will get backed up and will be delayed,
since it takes a considerable amount of time for data to be sent through the serial port.
Additionally, parts of the send queue will be all sent together until it reaches 0.5 seconds,
which may end up with unexpected behavior in some programs.
To prevent these problems, either make the value of `send_interval` larger,
or add a delay within the main thread. 

If the program has not waited long enough before sending, then the method will return `false`.

If `check_type` is True, then it will process each argument, then concatenate, encode, and send.

- If the argument is `bytes` then decodes to `str`
- If argument is `list` or `dict` then passes through `json.dumps`
- If argument is `set` or `tuple` then converts to list and passes through `json.dumps`
- Otherwise, directly convert to `str` and strip
Otherwise, converts each argument directly to `str` and then concatenates, encodes, and sends.

Parameters:

- `*args`: Everything that is to be sent, each as a separate parameter. Must have at least one parameter.
- `check_type` (bool)  : If types in *args should be checked. By default True.
- `ending` (str)  : The ending of the bytes object to be sent through the serial port. By default a carraige return + newline ("\\r\\n")
- `concatenate` (str)  : What the strings in args should be concatenated by. By default a space `' '`

Returns:

- `true` on success (everything has been sent through)
- `false` on failure (not open, not waited long enough before sending, did not fully send through, etc.)

#### Connection.receive()

```py
def receive(num_before=0)
```

Returns the most recent receive object

The IO thread will continuously detect receive data and put the `bytes` objects in the `rcv_queue`. 
If there are no parameters, the method will return the most recent received data.
If `num_before` is greater than 0, then will return `num_before`th previous data.

- Note: `num_before` must be less than the current size of the queue and greater or equal to 0 
    - If not, returns None (no data)
- Example:
    - 0 will return the most recent received data
    - 1 will return the 2nd most recent received data
    - ...

Parameters:

- `num_before` (int)  : Which receive object to return. Must be nonnegative. By default None.

Returns:

- A `tuple` representing the `(timestamp received, data in bytes)`
- `None` if no data was found or port not open

#### Connection.conv_bytes_to_str()

```py
def conv_bytes_to_str(rcv, read_until=None, strip=True)
```

Convert bytes receive object to a string.

Parameters:

- `rcv` (bytes): A bytes object. If None, then the method will return None.
- `read_until` (str, None): Will return a string that terminates with `read_until`, excluding `read_until`. 
For example, if the string was `"abcdefg123456\n"`, and `read_until` was `\n`, then it will return `"abcdefg123456"`.
If there are multiple occurrences of `read_until`, then it will return the string that terminates with the first one.
If `read_until` is None or it doesn't exist, the it will return the entire string. By default None.
- `strip` (bool): If True, then strips spaces and newlines from either side of the processed string before returning.
If False, returns the processed string in its entirety. By default True.

Returns:

- A `str` representing the data
- None if `rcv` is None

#### Connection.get()

```py
def get(given_type, read_until=None, strip=True)
```

Gets first response after this method is called.

This method differs from `receive()` because `receive()` returns
the last element of the receive buffer, which could contain objects
that were received before this function was called. This function
waits for something to be received after it is called until it either
gets the object or until the timeout is reached.

Parameters:

- `given_type` (type): either `bytes` or `str`, indicating which one to return. 
Will raise exception if type is invalid, REGARDLESS of `self.exception`. Example: `get(str)` or `get(bytes)`.
- `read_until` (str, None): Will return a string that terminates with `read_until`, excluding `read_until`. 
For example, if the string was `"abcdefg123456\n"`, and `read_until` was `\n`, then it will return `"abcdefg123456"`.
If there are multiple occurrences of `read_until`, then it will return the string that terminates with the first one.
If `read_until` is None or it doesn't exist, the it will return the entire string. By default None.
- `strip` (bool): If True, then strips spaces and newlines from either side of the processed string before returning.
If False, returns the processed string in its entirety. By default True.

Returns:

- None if no data received (timeout reached)
- A `bytes` object indicating the data received if `type` is `bytes`
- A `str` object indicating the data received, then passed through `conv_bytes_to_str()`, if `type` is `str`

#### Connection.get_all_rcv()

```py
def get_all_rcv()
```

Returns the entire receive queue

The queue will be a `queue_size`-sized list that contains
tuples (timestamp received, received bytes).

Returns:

- A list of tuples indicating the timestamp received and the bytes object received

#### Connection.get_all_rcv_str()

```py
def get_all_rcv_str(read_until=None, strip=True)
```

Returns entire receive queue as string.

Each bytes object will be passed into `conv_bytes_to_str()`.
This means that `read_until` and `strip` will apply to 
EVERY element in the receive queue before returning.

Parameters:

- `read_until` (str, None): Will return a string that terminates with `read_until`, excluding `read_until`. 
For example, if the string was `"abcdefg123456\n"`, and `read_until` was `\n`, then it will return `"abcdefg123456"`.
If there are multiple occurrences of `read_until`, then it will return the string that terminates with the first one.
If `read_until` is None or it doesn't exist, the it will return the entire string. By default None.
- `strip` (bool): If True, then strips spaces and newlines from either side of the processed string before returning.
If False, returns the processed string in its entirety. By default True.

Returns:

- A list of tuples indicating the timestamp received and the converted string from bytes 

#### Connection.get_first_response()

```py
def get_first_response(*args, is_bytes=True, check_type=True, ending='\r\n', concatenate=' ', read_until=None, strip=True)
```

Gets the first response from the serial port after sending something.

This method works almost the same as `send()` (see `self.send()`). 
It also returns a string representing the first response from the serial port after sending.
All `*args` and `check_type`, `ending`, and `concatenate`, will be sent to `send()`.

If there is no response after reaching the timeout, then it breaks out of the method.

Parameters:

- `*args`: Everything that is to be sent, each as a separate parameter. Must have at least one parameter.
- `is_bytes`: If False, then passes to `conv_bytes_to_str()` and returns a string
with given options `read_until` and `strip`. See `conv_bytes_to_str()` for more details.
If True, then returns raw `bytes` data. By default True.
- `check_type` (bool): If types in *args should be checked. By default True.
- `ending` (str): The ending of the bytes object to be sent through the serial port. By default a carraige return ("\\r\\n")
- `concatenate` (str): What the strings in args should be concatenated by. By default a space `' '`.

These parameters only apply is `is_bytes` is False:

- `read_until` (str, None): Will return a string that terminates with `read_until`, excluding `read_until`. 
For example, if the string was `"abcdefg123456\n"`, and `read_until` was `\n`, then it will return `"abcdefg123456"`.
If `read_until` is None, the it will return the entire string. By default None.
- `strip` (bool): If True, then strips the received and processed string of whitespace and newlines, then 
returns the result. If False, then returns the raw result. By default True.

Returns:

- A string or bytes representing the first response from the serial port.
- None if there was no connection (if self.exception == False), no data, timeout reached, or send interval not reached.

#### Connection.wait_for_response()

```py
def wait_for_response(response, after_timestamp=-1.0, read_until=None, strip=True)
```

Waits until the connection receives a given response.

This method will wait for a response that matches given `response`
whose time received is greater than given timestamp `after_timestamp`.

Parameters:

- `response` (str, bytes): The receive data that the program is looking for.
If given a string, then compares the string to the response after it is decoded in `utf-8`.
If given a bytes, then directly compares the bytes object to the response.
If given anything else, converts to string.
- `after_timestamp` (float): Look for responses that came after given time as the UNIX timestamp.
If negative, the converts to time that the method was called, or `time.time()`. By default -1.0

These parameters only apply if `response` is a string:

- `read_until` (str, None): Will return a string that terminates with `read_until`, excluding `read_until`. 
For example, if the string was `"abcdefg123456\n"`, and `read_until` was `\n`, then it will return `"abcdefg123456"`.
If `read_until` is None, the it will return the entire string. By default None.
- `strip` (bool): If True, then strips the received and processed string of whitespace and newlines, then 
returns the result. If False, then returns the raw result. By default True.

Returns:

- True on success
- False on failure: timeout reached because response has not been received.

#### Connection.send_for_response()

```py
def send_for_response(response, *args, read_until=None, strip=True, check_type=True, ending='\r\n', concatenate=' ')
```

Continues sending something until the connection receives a given response.

This method will call `send()` and `receive()` repeatedly (calls again if does not match given `response` parameter).
See `send()` for more details on `*args` and `check_type`, `ending`, and `concatenate`, as these will be passed to the method.
Will return `true` on success and `false` on failure (reached timeout)

Parameters:

- `response` (str, bytes): The receive data that the program looks for after sending.
If given a string, then compares the string to the response after it is decoded in `utf-8`.
If given a bytes, then directly compares the bytes object to the response.
- `*args`: Everything that is to be sent, each as a separate parameter. Must have at least one parameter.
- `check_type` (bool): If types in *args should be checked. By default True.
- `ending` (str): The ending of the bytes object to be sent through the serial port. By default a carraige return ("\\r\\n")
- `concatenate` (str): What the strings in args should be concatenated by. By default a space `' '`

These parameters only apply if `response` is a string:

- `read_until` (str, None): Will return a string that terminates with `read_until`, excluding `read_until`. 
For example, if the string was `"abcdefg123456\n"`, and `read_until` was `\n`, then it will return `"abcdefg123456"`.
If `read_until` is None, the it will return the entire string. By default None.
- `strip` (bool): If True, then strips the received and processed string of whitespace and newlines, then 
returns the result. If False, then returns the raw result. By default True.

Returns:

- `true` on success: The incoming received data matching `response`.
- `false` on failure: Connection not established (if self.exception == False), incoming data did not match `response`, or `timeout` was reached, or send interval has not been reached.

#### Connection.reconnect()

```py
def reconnect(timeout=None)
```

Attempts to reconnect the serial port.

This method will continuously try to connect to the ports provided in `__init__()`
until it reaches given `timeout` seconds. If `timeout` is None, then it will
continuously try to reconnect indefinitely.

Will raise `ConnectException` if already connected, regardless
of if `exception` is True or not.

Note that disconnecting the serial device will **reset** the receive and send queues.

Parameters:

- `timeout` (float, None)  : Will try to reconnect for
`timeout` seconds before returning. If None, then will try to reconnect
indefinitely. By default None.

Returns:

- True if able to reconnect
- False if not able to reconnect within given timeout

#### Connection.all_ports()

```py
def all_ports(**kwargs)
```

Lists all available serial ports.

Calls `tools.all_ports()`, which itself calls `serial.tools.list_ports.comports()`.
For more information, see [here](https://pyserial.readthedocs.io/en/latest/tools.html#module-serial.tools.list_ports).

Parameters: See link above.

Returns: A generator-like object (see link above)

#### Connection.custom_io_thread()

```py
def custom_io_thread(func)
```

A decorator custom IO thread rather than using the default one.

It is recommended to read `pyserial`'s documentation before creating a custom IO thread.

What the IO thread executes every 0.01 seconds will be referred to as a "cycle".

Note that this method should be called **before** `connect()` is called, or
else the thread will use the default cycle.

To see the default cycle, see the documentation of `BaseConnection`.

What the IO thread will do now is:

1. Check if anything is using (reading from/writing to) the variables
2. If not, copy the variables into a `SendQueue` and `ReceiveQueue` object.
3. Call the `custom_io_thread` function (if none, calls the default cycle)
4. Copy the results from the function back into the send queue and receive queue.
5. Rest for 0.01 seconds to rest the CPU

The cycle should be in a function that this decorator will be on top of.
The function should accept three parameters:

- `conn` (a `serial.Serial` object)
- `rcv_queue` (a `ReceiveQueue` object; see more on how to use it in its documentation)
- `send_queue` (a `SendQueue` object; see more on how to use it in its documentation)

To enable autocompletion on your text editor, you can add type hinting:

```py
from com_server import Connection, SendQueue, ReceiveQueue
from serial import Serial

conn = Connection(...)

# some code

@conn.custom_io_thread
def custom_cycle(conn: Serial, rcv_queue: ReceiveQueue, send_queue: SendQueue):
    # code here

conn.connect() # call this AFTER custom_io_thread()

# more code
``` 

The function below the decorator should not return anything.

#### Connection.connected

A property to determine if the connection object is currently connected to a serial port or not.
This also can determine if the IO thread for this object
is currently running or not.

Getter:

- A `bool` indicating if the current connection is currently connected

#### Connection.timeout

A property to determine the timeout of this object.

Getter:

- Gets the timeout of this object.

Setter:

- Sets the timeout of this object after checking if convertible to nonnegative float. 
Then, sets the timeout to the same value on the `pyserial` object of this class.
If the value is `float('inf')`, then sets the value of the `pyserial` object to None.

#### Connection.send_interval

A property to determine the send interval of this object.

Getter:

- Gets the send interval of this object.

Setter:

- Sets the send interval of this object after checking if convertible to nonnegative float.

#### Connection.conn_obj

A property to get the Serial object that handles sending and receiving.

Getter:

- Gets the Serial object.  

#### Connection.available

A property indicating how much new data there is in the receive queue.

Getter:

- Gets the number of additional data received since the user last called the `receive()` method.

#### Connection.port

Returns the current port of the connection

Getter:

- Gets the current port of the connection 

---

### com_server.ConnectionRoutes

A wrapper for Flask objects for adding routes involving a `Connection` object

This class allows the user to easily add REST API routes that interact
with a serial connection by using `flask_restful`.

When the connection is disconnected, a `500 Internal Server Error`
will occur when a route relating to the connection is visited.
A thread will detect this event and will try to reconnect the serial port.
Note that this will cause the send and receive queues to **reset**.

If a resource is accessed while it is being used by another process,
then it will respond with `503 Service Unavailable`.

More information on [Flask](https://flask.palletsprojects.com/en/2.0.x/) and [flask-restful](https://flask-restful.readthedocs.io/en/latest/).

#### ConnectionRoutes.\_\_init\_\_()

```py
def __init__(conn)
```

Constructor

Parameters:

- `conn` (`Connection`): The `Connection` object the API is going to be associated with.

There should only be one `ConnectionRoutes` object that wraps each `Connection` object.
Having multiple may result in an error.

Note that `conn` needs to be connected when starting
the server or else an error will be raised.

#### ConnectionRoutes.add_resource()

```py
def add_resource(resource)
```

Decorator that adds a resource

The resource should interact with the serial port.
If not, use `Api.add_resource()` instead.

This decorator works the same as [Api.resource()](https://flask-restful.readthedocs.io/en/latest/api.html#flask_restful.Api.resource).

However, the class under the decorator should
not extend `flask_restful.Resource` but
instead `com_server.ConnectionResource`. This is
because `ConnectionResource` contains `Connection`
attributes that can be used in the resource.

Unlike a resource added using `Api.add_resource()`,
if a process accesses this resource while it is
currently being used by another process, then it will
respond with `503 Service Unavailable`.

Currently, supported methods are:

- `GET`
- `POST`
- `PUT`
- `PATCH`
- `DELETE`
- `OPTIONS`
- `HEAD`

Make sure to put method names in lowercase

Parameters:

- `endpoint` (str): The endpoint to the resource.

#### ConnectionRoutes.all_resources

A property that returns a dictionary of resource paths mapped to resource classes.


---

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

---

### com_server.ConnectionResource

A custom resource object that is built to be used with `RestApiHandler` and `ConnectionRoutes`.

This class is to be extended and used like the `Resource` class.
Have `get()`, `post()`, and other methods for the types of responses you need.

---

### com_server.api

This is the server API module for the built-in endpoints of COM-Server.

See the [Server API](../../server).

---

### com_server.SendQueue

The send queue object.

This object is like a queue but cannot be iterated through. 
It contains methods such as `front()` and `pop()`, just like
the `queue` data structure in C++. However, objects cannot
be added to it because objects should only be added through
the `send()` method. 

Makes sure the user only reads and pops from send queue
and does not directly add or delete anything from the queue.

#### SendQueue.\_\_init\_\_()

```py
def __init__(send_queue)
```

Constructor for the send queue object.

Parameters:

- `send_queue` (list): The list that will act as the send queue

Returns:

- Nothing

#### SendQueue.front()

```py
def front()
```

Returns the first element of the send queue.

Raises an `IndexError` if the length of the send queue is 0.

Parameters:

- None

Returns:

- The bytes object to send 

#### SendQueue.pop()

```py
def pop()
```

Removes the first index from the queue.

Raises an `IndexError` if the length of the send queue is 0.

Parameters:

- None

Returns:

- None

#### SendQueue.copy()

```py
def copy()
```

Returns a shallow copy of the send queue list. 

Using this to copy to a list may be dangerous, as
altering elements in the list may alter the elements
in the send queue itself. To prevent this, use the
`deepcopy()` method.

Parameters:

- None

Returns:

- A shallow copy of the send queue

#### SendQueue.deepcopy()

```py
def deepcopy()
```

Returns a deepcopy of the send queue list.

By using this, you can modify the list without altering
any elements of the actual send queue itself. However,
it is a little more resource intensive.

Parameters:

- None

Returns:

- A deep copy of the send queue

---

### com_server.ReceiveQueue

The ReceiveQueue object.

This object is a queue, but the user can 
only add bytes object(s) to it. 

Makes sure the user does not directly add,
delete, or modify the queue. 

#### ReceiveQueue.\_\_init\_\_()

```py
def __init__(rcv_queue, queue_size)
```

Constructor for the send queue object.

Parameters:

- `rcv_queue` (list): The list that will act as the receive queue.
- `queue_size` (int): The maximum size of the receive queue

Returns:

- Nothing 

#### ReceiveQueue.pushitems()

```py
def pushitems(*args)
```

Adds a list of items to the receive queue.

All items in `*args` must be a `bytes` object. A
`TypeError` will be raised if not.

If the size exceeds `queue_size` when adding, then
it will pop the front of the queue. 

A tuple (timestamp, bytes) will be added. The timestamp
will be regenerated for each iteration of the for loop
so they will be in order when binary searching.

Parameters:

- `*args`: The bytes objects to add

Returns:

- Nothing

#### ReceiveQueue.copy()

```py
def copy()
```

Returns a shallow copy of the receive queue list. 

The receive queue list will be a list of tuples:

- (timestamp, bytes data)

Using this to copy to a list may be dangerous, as
altering elements in the list may alter the elements
in the receive queue itself. To prevent this, use the
`deepcopy()` method.

Parameters:

- None

Returns:

- A shallow copy of the receive queue

#### ReceiveQueue.deepcopy()

```py
def deepcopy()
```

Returns a deepcopy of the receive queue.

The receive queue list will be a list of tuples:

- (timestamp, bytes data)

By using this, you can modify the list without altering
any elements of the actual send queue itself. However,
it is a little more resource intensive.

Parameters:

- None

Returns:

- A deep copy of the receive queue

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
