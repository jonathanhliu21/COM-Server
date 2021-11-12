#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
An example of how to use the Connection object.

NOTE: the sketch located in examples/send_back needs
to be uploaded to the Arduino before running this script.
"""

import time

from com_server import Connection

# make the Connection object
conn = Connection(baud=115200, port="/dev/ttyUSB0")
# conn = Connection(baud=115200, port="/dev/ttyUSB...") # if Linux; can be "/dev/ttyACM..."
# conn = Connection(baud=115200, port="/dev/cu.usbserial...") 
# conn = Connection(baud=115200, port="COM...") # if Windows

conn.connect() # connect to serial port

while (conn.connected):
    # continue running as long as there is a connection established

    # send current time
    # make ending a newline and remove the carriage return, as the Arduino program reads Serial strings until the newline
    send_str = "Sending at: {}".format(time.time())
    conn.send(send_str, ending='\n') 
    print(send_str) # for comparing with below

    # get first response from the serial port after sending
    # read until the newline as pyserial prints with newline at end
    # strip result
    # should be `Got: "[What was printed above]"`
    print(conn.get(str, read_until='\n', strip=True))

    # there is an interval between sending data
    # if the program tries to send too rapidly, then it will not send
    # wait for it to be able to send again
    # by default, the send interval is 1
    time.sleep(1) 

# call disconnect(), as variable will not be used anymore
conn.disconnect()
