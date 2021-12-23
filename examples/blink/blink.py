#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
An example of writing data to an Arduino.

This sketch will ask for an input, and the
built-in LED on the Arduino should turn on,
blink, or turn off based on different inputs.

NOTE: The sketch located in examples/blink must
be uploaded to an Arduino before running this script.
"""

import time

from com_server import Connection

# make the Connection object; make send_interval 0.1 seconds because not sending large data
conn = Connection(baud=115200, port="/dev/ttyUSB0", send_interval=0.1) # if Linux
# conn = Connection(baud=115200, port="/dev/ttyUSB...", send_interval=0.1) # if Linux; can be "/dev/ttyACM..."
# conn = Connection(baud=115200, port="/dev/cu.usbserial...", send_interval=0.1) # if Mac
# conn = Connection(baud=115200, port="COM...", send_interval=0.1) # if Windows

with conn:
    # use a context manager, which will connect and disconnect 
    # automatically when entering and exiting.

    while conn.connected:
        # continue running as long as there is a connection established

        cmd = input("Enter LED state: (s)olid, (b)link, (o)ff, or (e)xit: ")

        if cmd == "e" or cmd == "exit":
            break
        elif cmd == "s" or cmd == "solid":
            conn.send("s", ending='\n')
        elif cmd == "b" or cmd == "blink":
            conn.send("b", ending='\n')
        elif cmd == "o" or cmd == "off":
            conn.send("o", ending='\n')
        else:
            print("Command not recognized; please try again.")

        # Recommended to include a delay when using connection
        # object in a loop
        time.sleep(0.01)
