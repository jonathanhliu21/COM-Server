#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A file containing constants for COM-Server.
"""

# timeouts & send intervals
NO_TIMEOUT = float("inf")
NO_SEND_INTERVAL = 0

# serial baud rates
NORMAL_BAUD_RATE = 9600
FAST_BAUD_RATE = 115200

# receive queue
NO_RCV_QUEUE = 1 # not 0 because the program would then disregard all incoming data
RCV_QUEUE_SIZE_XSMALL = 32
RCV_QUEUE_SIZE_SMALL = 128
RCV_QUEUE_SIZE_NORMAL = 256
RCV_QUEUE_SIZE_LARGE = 512
RCV_QUEUE_SIZE_XLARGE = 1024

# server
DEFAULT_HOST="0.0.0.0"
DEFAULT_PORT=8080
