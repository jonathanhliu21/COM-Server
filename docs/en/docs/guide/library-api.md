# COM-Server Library API

## Classes

### com_server.BaseConnection
A base connection object with a serial or COM port.

If you want to communicate via serial, it is recommended to
either directly use `pyserial` directly or use the `Connection` class.

How this works is that it creates a pyserial object given the parameters, which opens the connection. 
The user can manually open and close the connection. It is closed by default when the initializer is called.
It spawns a thread that continuously looks for serial data and puts it in a buffer. 
When the user wants to send something, it will pass the send data to a queue,
and the thread will process the queue and will continuously send the contents in the queue
until it is empty, or it has reached 0.5 seconds. This thread is referred as the "IO thread".

All data will be encoded and decoded using `utf-8`.

If used in a `while(true)` loop, it is highly recommended to put a `time.sleep()` within the loop,
so the main thread won't use up so many resources and slow down the IO thread.

This class contains the four basic methods needed to talk with the serial port:

- `connect()`: opens a connection with the serial port
- `disconnect()`: closes the connection with the serial port
- `send()`: sends data to the serial port
- `read()`: reads data from the serial port

It also contains the property `connected` to indicate if it is currently connected to the serial port.

**Warning**: Before making this object go out of scope, make sure to call `disconnect()` in order to avoid thread leaks. If this does not happen, then the disconnect thread and IO thread will still be running for an object that has already been deleted.

#### com_server.\_\_init\_\_()

```py
def __init__(baud, port, exception=True, timeout=1, queue_size=256, handle_disconnect=True, exit_on_disconnect=True, **kwargs)
```

Initializes the Base Connection class. 

`baud`, `port`, `timeout`, and `kwargs` will be passed to pyserial.  
For more information, see [here](https://pyserial.readthedocs.io/en/latest/pyserial_api.html#serial.Serial).

Parameters:

- `baud` (int): The baud rate of the serial connection 
- `port` (str): The serial port
- `timeout` (float) (optional): How long the program should wait, in seconds, for serial data before exiting. By default 1.
- `exception` (bool) (optional): Raise an exception when there is a user error in the methods rather than just returning. By default True.
- `send_interval` (int) (optional): Indicates how much time, in seconds, the program should wait before sending another message. 
Note that this does NOT mean that it will be able to send every `send_interval` seconds. It means that the `send()` method will 
exit if the interval has not reached `send_interval` seconds. NOT recommended to set to small values. By default 1.
- `queue_size` (int) (optional): The number of previous data that was received that the program should keep. Must be nonnegative. By default 256.
- `handle_disconnect` (bool) (optional): Whether the program should spawn a thread to detect if the serial port has disconnected or not. By default True.
- `exit_on_disconnect` (bool) (optional): If the program should exit if serial port disconnected. Does NOT work on Windows. By default False.
- `kwargs`: Will be passed to pyserial.

Returns: nothing

#### com_server.connect()

```py
def connect()
```

Begins connection to the serial port.

When called, initializes a serial instance if not initialized already. Also starts the receive thread.

Parameters: None

Returns: None

May raise:

- `com_server.ConnectException` if the user calls this function while it is already connected and `exception` is True.
- `serial.serialutil.SerialException` if the port given in `__init__` does not exist.
- `EnvironmentError` if `exit_on_disconnect` is True and the user is on Windows (_not tested_).

#### com_server.disconnect()

```py
def disconnect()
```

Closes connection to the serial port.

When called, calls `Serial.close()` then makes the connection `None`. If it is currently closed then just returns.

**NOTE**: This method should be called if the object will not be used anymore
or before the object goes out of scope, as deleting the object without calling 
this will lead to stray threads.

Parameters: None

Returns: None

#### com_server.send()

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
- `check_type` (bool) (optional): If types in *args should be checked. By default True.
- `ending` (str) (optional): The ending of the bytes object to be sent through the serial port. By default a carraige return + newline ("\\r\\n")
- `concatenate` (str) (optional): What the strings in args should be concatenated by. By default a space `' '`

Returns:

- `true` on success (everything has been sent through)
- `false` on failure (not open, not waited long enough before sending, did not fully send through, etc.)

May raise:
- `com_server.ConnectException` if the user tries to send while it is disconnected and `exception` is True.

#### com_server.receive()

```py
def receive(num_before=0)
```

Returns the most recent receive object

The receive thread will continuously detect receive data and put the `bytes` objects in the `rcv_queue`. 
If there are no parameters, the method will return the most recent received data.
If `num_before` is greater than 0, then will return `num_before`th previous data.

- Note: Must be less than the current size of the queue and greater or equal to 0 
    - If not, returns None (no data)
- Example:
    - 0 will return the most recent received data
    - 1 will return the 2nd most recent received data
    - ...

Note that the data will be read as ALL the data available in the serial port,
or `Serial.read_all()`.

Parameters:

- `num_before` (int) (optional): Which receive object to return. Must be nonnegative. By default None.

Returns:

- A `tuple` representing the `(timestamp received, data in bytes)`
- `None` if no data was found or port not open

May raise:

- `com_server.ConnectException` if a user calls this method when the object has not been connected and `exception` is True.
- `ValueError` if `num_before` is nonnegative and `exception` is True.

#### com_server.connected

Getter:  
A property to determine if the connection object is currently connected to a serial port or not.
This also can determine if the IO thread and the disconnect thread for this object
are currently running or not.

## Exceptions

### com_server.ConnectException  

This exception is raised whenever a user tries to do an operation with the `Connection` class while it is disconnected, but the operation requires it to be connected, or vice versa.

### com_server.EndpointExistsException

This exception is raised if the user tries to add a route to the `RestApiHandler` that already exists.
