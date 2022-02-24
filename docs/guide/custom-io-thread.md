# Making a custom IO thread

The default IO thread in the `Connection` object may be limiting, which is why you may consider making a custom IO thread.

Before you start, you need to know how the program handles IO threads in the first place. Note that this only applies to `Connection` objects, not `BaseConnection`. 

The `Connection` object handles input and output from the serial port in a separate daemon thread, hence the name "IO Thread". The thread will run until the serial port is disconnected, which raises an exception, and can be respawned with the `reconnect()` method. 

This thread shares variables with a **send queue** and **receive queue**. The send queue contains the data from each time the program has called `send()`, whether it is from `send()` itself or a `Connection` method that calls `send()`, and it has a maximum size of 65536. The receive queue contains the data that has been previously received from the serial port, and this is what is referenced when the `receive()` and `receive()`-based methods such as `get()` is called. 

Generally, your IO thread should be consistent in removing items from the send queue to send through the serial port and putting received items into the receive queue.

### Creating a custom function

To get started, use the `Connection.custom_io_thread()` decorator above a custom function. This needs to be declared before `connect()` is called, or if using a context manager, before the context manager is entered, or the program will use the default IO thread.

```py
import time

from com_server import Connection

conn = Connection(115200, "<port1>", "<port2>") # change <port1> and <port2>; feel free to add extra arguments

@conn.custom_io_thread
def my_io_thread(conn, rcv_queue, send_queue):
    # name of function can be anything
    pass

with conn:
    # rest of code
    pass
```

Note the three parameters that the function needs to have:

- `conn` represents the pyserial `Serial` object ([docs](https://pyserial.readthedocs.io/en/latest/pyserial_api.html#serial.Serial))
- `rcv_queue` represents the com_server `ReceiveQueue` object ([docs](../library-api/#com_serversendqueue))
- `send_queue` represents the com_server `SendQueue` object ([docs](../library-api/#com_serverreceivequeue))

This is how the program will execute the IO thread now:

1. Since the receive queue and send queue are shared between the main thread and IO thread, the IO thread will wait for the thread lock to be freed (i.e. for those variables to not be used by the main thread), then copy the shared receive queue and send queue (which are native Python lists) to temporary `ReceiveQueue` and `SendQueue` objects. Then, it will release the thread lock.
2. The IO thread will execute the function declared by the user from the `custom_io_thread` decorator, passing in the three arguments. The temporary `ReceiveQueue` and `SendQueue` objects should be altered afterwords.
3. Again, the thread will wait for the send queue and receive queue to stop being used. When they are, it will copy the temporary `ReceiveQueue` back to the original receive queue. Then, it will pop all the elements that were used in the temporary `SendQueue` in the original send queue. It does this by comparing the initial size of the temporary `SendQueue` before running the function with the final size of the queue after running the function. The number of elements removed from the queue is the difference between the final size and initial size.
4. Sleep for 0.01 seconds to rest the CPU if `rest_cpu` is True (which it is by default)

The IO thread will continue doing these 4 things until the program is stopped or until the device disconnects.

The default function, or the default IO thread, does these things each time the function is called:

1. Checks if there is any data to be received
2. If there is, reads **all** the data and puts the `bytes` received into the receive queue
3. Tries to send everything in the send queue; breaks when 0.5 seconds is reached (will continue if send queue is empty)

### In the custom function

You could do anything you want, really. However, there are some things to note:

1. The `Serial` object only supports reading and writing `bytes`, not `str`.
2. The `SendQueue` object only supports popping and objects cannot be inserted. It stores `bytes` objects, not `str`.
3. The `ReceiveQueue` object only supports inserting and objects cannot be removed. All objects inserted must be `bytes`. It will actually store a tuple `(timestamp inserted, bytes object)` internally, not just the bytes object. This means that if you insert multiple items in one cycle of the loop, then those objects will all have different timestamps.
4. The function will be called in a **thread** and the variables are **not** thread-safe. Use a thread lock when copying a global variable.

### Useful documentation links

- [pyserial `Serial` object](https://pyserial.readthedocs.io/en/latest/pyserial_api.html#serial.Serial)
- [`SendQueue`](../library-api/#com_serversendqueue)
- [`ReceiveQueue`](../library-api/#com_serverreceivequeue)

### Example

This example shows an IO thread that sends all its data but instead of properly putting the received data from the serial port into the receive queue, it will put a bytes object reading `b"Hello world!"` instead.

```py
import time

from com_server import Connection

conn = Connection(115200, "<port1>", "<port2>") # change <port1> and <port2>; feel free to add extra arguments

@conn.custom_io_thread
def my_io_thread(conn, rcv_queue, send_queue):
    # name of function can be anything

    # sending data (send one at a time in queue for 0.5 seconds)
    st_t = time.time()  # start time
    while time.time() - st_t < 0.5:
        if len(send_queue) > 0:
            conn.write(send_queue.front())  # write the front of the send queue
            conn.flush()
            send_queue.pop()  # pop the queue
        else:
            # break out if all sent
            break
        time.sleep(0.01)
    
    # push "Hello world" into receive queue
    rcv_queue.pushitems(b"Hello world!")

with conn:
    # rest of code

    while conn.connected:
        conn.send("Hello at", time.time(), ending='\n')
        r = conn.receive_str()
        if (r is not None):
            print(r[1]) # should be "Hello world!"
        
        time.sleep(0.01)
```