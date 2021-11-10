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

####

## Exceptions

### com_server.ConnectException  

This exception is raised whenever a user tries to do an operation with the `Connection` class while it is disconnected, but the operation requires it to be connected, or vice versa.

### com_server.EndpointExistsException

This exception is raised if the user tries to add a route to the `RestApiHandler` that already exists.
