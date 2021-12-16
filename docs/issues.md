# Known issues

A list of known issues with COM-Server.

## Sending/receiving long strings of data

Sending or reading anything longer than 50 characters may lead to partial data readings using the default IO thread. This is because it takes time to read the data, and if there is too much being sent over a longer period of time, then the program would think that there is less data to be read from the serial buffer than there actually is. On MacOS, this number was around 20 characters, so I added a short delay when reading the data to account for the time that the data takes to be read.

This means that on Linux and Windows, sending/receiving large amounts of data will lead to wrong data readings, and on Mac, sending/receiving large amounts of data may lead to slower IO (because of the way the IO thread is written).

It is recommended that you write your **own** IO thread using `Connection.custom_io_thread()`.
