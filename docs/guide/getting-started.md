# Getting started with COM-Server

This page will show you the basics of getting started with COM-Server.

## Creating a Connection class

```py
import com_server

conn = com_server.Connection(port="<port>", baud=<baud>)
```

Each Serial port has a port and a baud rate. The port varies from operating system to operating system. For example:

- On Linux, the port is in the `/dev` directory and begins with `tty` followed by some letters and numbers (e.g. `/dev/ttyUSB0`, `/dev/ttyUSB1`, `/dev/ttyACM0`).
- On Mac OS, the port is also in the `/dev` directory and begins with `cu.` then a sequence of letters and numbers. If it is a USB port, then it would be `cu.usbserial` followed by a string of letters/numbers (`/dev/cu.usbserial-A1252381`) 
- On Windows, the port usually begins with `COM` (e.g. `COM3`).

A good way of determining the port is by disconnecting the serial port, typing in the command below, connecting the port, then entering the command again. The one that shows up is the one that you would use.

```sh
> pyserial-ports
```

If `/dev/ttyUSB0` is the one that shows up after the connection, then we would write it like this:

```py
import com_server

conn = com_server.Connection(port="/dev/ttyUSB0", baud=<baud>)
```

The baud rate is necessary for serial ports because it determines the speed that data should be transferred at, in bits per second. The standard baud rates can be seen [here](https://lucidar.me/en/serialib/most-used-baud-rates-table/), with the ones that are most commonly used bolded.

Example:

Opening a port at `/dev/ttyUSB0` with baud rate `115200`:
```py
import com_server

conn = com_server.Connection(port="/dev/ttyUSB0", baud=115200)
```

`115200` and `9600` are the ones most commonly used with Arduino using `Serial.begin()`:

```cpp
void setup(){
    Serial.begin(9600);
    // setup code
}

void loop(){
    // loop code
}
```

It is always recommended to use a timeout. The default timeout is 1 second. Below is an example of a port opened at `/dev/ttyUSB0` with baud rate `115200` and a timeout of 2 seconds:
```py
import com_server

conn = com_server.Connection(port="/dev/ttyUSB0", baud=115200, timeout=2)
```

#### Multiple ports

If you want to try multiple ports, then you can put them as arguments like this:

```py
import com_server

conn = com_server.Connection(115200, "/dev/ttyUSB0", "/dev/ttyUSB1", "/dev/ttyACM0", "/dev/ttyACM1", timeout=1, send_interval=1)
```

In this example, the program will try to connect to `/dev/ttyUSB0` with baud rate 115200. If that fails, then it will try to connect to `/dev/ttyUSB1`, and so on. It will establish a connection with the **first** port that succeeds.

### Connecting and disconnecting

This is when the object actually connects to the serial port. When this happens, it spawns a thread called the IO thread which handles sending and receiving data to and from the serial port.

When disconnecting the object, it will delete the IO thread and reset its IO variables, including the send queue and the list of received data.

There are two ways of doing this:

* Using the `connect` and `disconnect` methods

```py
conn.connect()

# do stuff with the connection object

conn.disconnect()
```

**Important:** Remember to always call the `disconnect()` method if the object will not be used anymore, or there may be stray threads in your program.

* Using a context manager:

```py
with com_server.Connection(port="/dev/ttyUSB0", baud=115200) as conn:
    # do stuff with connection object
```

The context manager will connect the object automatically as it enters and disconnect it automatically when it exits, so you do not have to worry about calling `disconnect()` before deleting the object.

To check if the connection object is currently connected or not, use the `connected` property:

```py
print(conn.connected)
```

### Reconnecting

On the event of a disconnect, you can call the `reconnect()` method to try to reconnect to a port provided in `__init__()`. However, it will raise a `ConnectException` if the port is already connected and this is called.

Note that disconnecting the serial device will **reset** the receive and send queues.

```py
with Connection(...) as conn:
    while True:
        # It is recommeded to put operations in try-except because
        # methods may raise ConnectException if the device disconnects
        # while in the middle of the loop.
        try:
            while conn.connected:
                # -------------------------------
                # do things with connection here
                # -------------------------------

                time.sleep(0.01) # recommeded to delay in main thread if in loop

            # in case it exits without errors
            conn.reconnect(timeout=None)
        except ConnectException:
            # ConnectException could be thrown if it is disconnected in the middle
            # of the loop, right before a send() or receive() method call.

            # If timeout is given, then it will try to reconnect within that timeout
            # and if it is not reconnected, then it will exit and return False.
            # 
            # If no timeout is given, then it will try to reconnect indefinitely.
            conn.reconnect(timeout=None)
```

### Sending 

To send data to the serial port, use the `send()` method. Put the data you want to send as arguments inside the send method. 

```py
# will send "a b c 1 2 3\r\n" without the quotations
conn.send("a", "b", "c", 1, 2, 3) 
```

To control what your arguments should be concatenated by, use the `concatenate` option:

```py
# will send "a;b;c;1;2;3\r\n" without the quotations
conn.send("a", "b", "c", 1, 2, 3, concatenate=';')
```

By default the `concatenate` option is a whitespace character.

To control what should be appended at the end before sending, use the `ending` option:

```py
# will send "a;b;c;1;2;3\n" without the quotations
conn.send("a", "b", "c", 1, 2, 3, ending='\n')
```
By default the `ending` option is a carraige return: `\r\n`.

Note that sending data too quickly will cause this function to return immediately without sending. This is because it takes time to send things through the serial port and sending data too rapidly may lead to data loss. To customize the interval between sending, use the `send_interval` option in the constructor of this class. The default is 1 second between sending.

If the timeout is reached, the method will return.

### Receiving

To get the data that came in from the serial port most recently, use the `receive()` method:

```py
rcv = conn.receive() # gets bytes object
rcv = conn.receive_str() # gets string object
```

To get the next most data that came in from the serial port:
```py
rcv = conn.receive(num_before=1) # gets bytes object
rcv = conn.receive_str(num_before=1) # gets string object
```

Increase the value of `num_before` to get the next most recent, next next more recent, etc. received data. 

If there has not been any received data, then returns `None`.

To wait for data to be received, use the `get()` method:

```py
rcv = conn.get(bytes) # gets first bytes after the method is called
rcv = conn.get(str) # gets first string after method is called
```

If no data gets received before the timeout is reached, then the method will return `None`.

### Full example

This example sends something to the serial port and then prints the first data that comes from the serial port after sending.

```py
import time
from com_server import Connection

conn = Connection(port="/dev/ttyUSB0", baud=115200)

conn.connect()

while conn.connected:
    conn.send("Sending something", ending="\n")
    received = conn.get(str)

    print(received)
    
    time.sleep(1) # wait one second between sending 

conn.disconnect()
```

## Creating a ConnectionRoutes class

`ConnectionRoutes` works similarly to a `flask_restful.Api` object but with only the `resource` decorator. It takes in a `Connection` object and it adds resources that are meant to interact with the `Connection` objects. What this means is that unlike `flask_restful.Api.resource()`, `ConnectionRoutes.add_resource()` gives the class a `conn` attribute representing the `Connection` that you can interact with in the HTTP methods. It also checks if the serial connection is currently being used, and if it is, it will respond with a `503 Service Unavailable`. Lastly, it checks if the connection is disconnected, and if so, it will respond with a `500 Internal Server Error`.

The class that the decorator is wrapping must extend `ConnectionResource`.

However, the server can be started separately with `start_app`, and the Flask object is not part of `ConnectionRoutes`, giving the user more flexibility, unlike the old `RestApiHandler`.

```py
from com_server import Connection, ConnectionRoutes, ConnectionResource, start_app
from flask import Flask
from flask_restful import Api

app = Flask(__name__)
api = Api(app)

conn = Connection(115200, "/dev/ttyUSB0") # change to your own port
handler = ConnectionRoutes(conn)

# Add your own resources that do not interact with the serial port here with `app` and `api`

@handler.add_resource("/hello_world")
class Hello_World_Resource(ConnectionResource):
    """
    This resource will return the most recently received object
    on GET and send "Hello world" to the serial device on POST.

    The URL to this resource would be localhost:8080/hello_world
    """

    def get(self):
        return {
            "data": self.conn.receive_str()
        }
    
    def post(self):
        self.conn.send("Hello world", ending="\n")
        return {
            "message": "sent"
        }

# app.run() cannot be used because the serial port is disconnected.
# We have to use start_app(), which automatically connects the serial port
# before running a production server with waitress on http://0.0.0.0:8080

start_app(app, api, handler)

# Note that start_app calls sys.exit(), so nothing should go after start_app
```

## Using the builtin endpoints

COM-Server comes with a list of builtin endpoints, with each one versioned. The latest version is the V1 API, with supports the `ConnectionRoutes` object. The previous version, V0, uses the old `RestApiHandler` and I do not recommend using it. However, its usage can be found [here](../../server/v0).

`com_server` has an `api` module that contains all the versions of the builtin endpoints. Note that version V0 is not compatible with version V1 because it uses a completely different handler class.

```py
from com_server import Connection, ConnectionRoutes, start_app
from com_server.api import V1
from flask import Flask
from flask_restful import Api

app = Flask(__name__)
api = Api(app)

conn = Connection(<baud>, "<serport>") 
handler = ConnectionRoutes(conn)

# add your own routes and endpoints here

V1(handler)
start_app(app, api, handler)
```

`V1` has an option `prefix`, indicating the prefix of all the routes in the builtin API. The default is `v1`, meaning that all version 1 API endpoints are prefixed with /v1/ (e.g. localhost:8080/v1/send).

Note that if you put V1 right before `start_app` and you have a resource that has the same path as one of the resources in the builtins, then the builtin resource will override your provided resource.

For more information on the builtin endpoints and routes, check out the [Version 1 API docs](../../server/v1).

## Using the CLI

COM-Server provides a command line tool to run the server given serial ports and a baud rate with the builtin V1 API. In your terminal, type in:

```sh
> com_server --help
```

for more information.
