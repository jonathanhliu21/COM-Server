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

### Connecting and disconnecting

This is when the object actually connects to the serial port. When this happens, it spawns two threads: one called the "IO thread" which handles sending and receiving data to and from the serial port, and one called the "disconnect thread," which handles disconnect detection.

When disconnecting the object, it will delete these two threads and reset its IO variables, including the send queue and the list of received data.

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

On the event of a disconnect, you can call the `reconnect()` function to try to reconnect to a new port. However, it will raise a `ConnectException` if the port is already connected and this is called.

```py
conn.reconnect() # will connect to previous port
conn.reconnect(port="/dev/ttyUSB1") # will change port to /dev/ttyUSB1 and reconnect there
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

To wait for the first data to be received, use the `get()` method:

```py
rcv = conn.get(bytes) # gets first bytes after the method is called
rcv = conn.get(str) # gets first string after method is called
```

If the timeout is reached, then the method will return `None`.

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



