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