#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Provides a set of functions that could be generally useful.
"""

import copy
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
    and does not add or delete anything from the queue.
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
        - A shallow copy of the list.
        """
    
        return self._send_queue.copy()

    def deepcopy(self) -> list:
        """Returns a deepcopy of the list.

        By using this, you can modify the list without altering
        any elements of the actual send queue itself. However,
        it is a little more resource intensive.

        Parameters:
        - None

        Returns:
        - A deep copy of the list
        """

        return copy.deepcopy(self._send_queue)
