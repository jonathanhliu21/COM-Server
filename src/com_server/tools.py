#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Provides a set of functions that could be generally useful.
"""

import copy
import time
import typing as t

import serial
import serial.tools.list_ports

def all_ports(**kwargs) -> t.Any:
    """Gets all ports from serial interface.

    Gets ports from Serial interface by calling `serial.tools.list_ports.comports()`.
    See [here](https://pyserial.readthedocs.io/en/latest/tools.html#module-serial.tools.list_ports) for more info.
    """

    return serial.tools.list_ports.comports(**kwargs)

class SendQueue:
    """The send queue object

    This object is like a queue but cannot be iterated through. 
    It contains methods such as `front()` and `pop()`, just like
    the `queue` data structure in C++. However, objects cannot
    be added to it because objects should only be added through
    the `send()` method. 

    Makes sure the user only reads and pops from send queue
    and does not directly add or delete anything from the queue.
    """

    def __init__(self, send_queue: list) -> None:
        """Constructor for send queue object.

        Parameters:
        - `send_queue` (list): The list that will act as the send queue 

        Returns:
        - Nothing
        """

        self._send_queue = send_queue
    
    def __len__(self) -> int:
        """
        Returns length of send queue
        """

        return len(self._send_queue)
    
    def __repr__(self) -> str:
        """
        String representation of queue
        """

        return f"SendQueue{self._send_queue}"
    
    def front(self) -> bytes:
        """Returns the first element of the send queue.

        Raises an `IndexError` if the length of the send queue is 0.

        Parameters:
        - None

        Returns:
        - The bytes object to send 
        """

        return self._send_queue[0]
    
    def pop(self) -> None:
        """Removes the first index from the queue.

        Raises an `IndexError` if the length of the send queue is 0.

        Parameters:
        - None
        
        Returns:
        - None
        """

        self._send_queue.pop(0)
    
    def copy(self) -> list:
        """Returns a shallow copy of the send queue list. 

        Using this to copy to a list may be dangerous, as
        altering elements in the list may alter the elements
        in the send queue itself. To prevent this, use the
        `deepcopy()` method.

        Parameters:
        - None

        Returns:
        - A shallow copy of the send queue
        """
    
        return self._send_queue.copy()

    def deepcopy(self) -> list:
        """Returns a deepcopy of the send queue list.

        By using this, you can modify the list without altering
        any elements of the actual send queue itself. However,
        it is a little more resource intensive.

        Parameters:
        - None

        Returns:
        - A deep copy of the send queue
        """

        return copy.deepcopy(self._send_queue)

class ReceiveQueue:
    """The ReceiveQueue object.
    
    This object is a queue, but the user can 
    only add bytes object(s) to it. 

    Makes sure the user does not directly add,
    delete, or modify the queue. 
    """

    def __init__(self, rcv_queue: list, queue_size: int) -> None:
        """Constructor for send queue object.

        Parameters:
        - `rcv_queue` (list): The list that will act as the receive queue.
        - `queue_size` (int): The maximum size of the receive queue

        Returns:
        - Nothing 
        """

        self._rcv_queue = rcv_queue
        self._queue_size = queue_size
    
    def __len__(self) -> int:
        """
        Returns the length of the receive queue.
        """

        return len(self._rcv_queue)
    
    def __repr__(self) -> str:
        """
        String representation of queue.
        """

        return f"ReceiveQueue{self._rcv_queue}"
    
    def additems(self, *args) -> None:
        """Adds a list of items to the receive queue.

        All items in `*args` must be a `bytes` object. A
        `TypeError` will be raised if not.

        If the size exceeds `queue_size` when adding, then
        it will pop the front of the queue. 

        A tuple (timestamp, bytes) will be added. The timestamp
        will be regenerated for each iteration of the for loop
        so they will be in order when binary searching.
        """

        for obj in args:
            if (not isinstance(obj, bytes)):
                raise TypeError("Every argument must be a bytes object")
            
            # add timestamp, obj to queue
            self._rcv_queue.append((time.time(), obj))

            if (len(self._rcv_queue) > self._queue_size):
                # if greater than queue size, then pop first element
                self._rcv_queue.pop(0)

    def copy(self) -> list:
        """Returns a shallow copy of the receive queue list. 

        Using this to copy to a list may be dangerous, as
        altering elements in the list may alter the elements
        in the receive queue itself. To prevent this, use the
        `deepcopy()` method.

        Parameters:
        - None

        Returns:
        - A shallow copy of the receive queue
        """
    
        return self._rcv_queue.copy()

    def deepcopy(self) -> list:
        """Returns a deepcopy of the receive queue.

        By using this, you can modify the list without altering
        any elements of the actual send queue itself. However,
        it is a little more resource intensive.

        Parameters:
        - None

        Returns:
        - A deep copy of the receive queue
        """

        return copy.deepcopy(self._rcv_queue)