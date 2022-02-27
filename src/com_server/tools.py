#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Provides a set of functions that could be generally useful.
"""

import copy
import time
import typing as t

from serial.tools.list_ports import comports


def all_ports(**kwargs: t.Any) -> t.Any:
    """Gets all ports from serial interface.

    Gets ports from Serial interface by calling `serial.tools.list_ports.comports()`.
    See [here](https://pyserial.readthedocs.io/en/latest/tools.html#module-serial.tools.list_ports) for more info.
    """

    return comports(**kwargs)


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

    def __init__(self, send_queue: t.List[bytes]) -> None:
        """Constructor for send queue object

        Args:
            send_queue (List[bytes]): The list that will act as the send queue
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
        """Returns the first element of the send queue

        Raises
            IndexError: If length of send queue is 0

        Returns:
            bytes: The bytes object to send
        """

        return self._send_queue[0]

    def pop(self) -> None:
        """Removes the first index from the queue.

        Raises:
            IndexError: If length of send queue is 0
        """

        self._send_queue.pop(0)

    def copy(self) -> t.List[bytes]:
        """Returns a shallow copy of the send queue list

        Using this to copy to a list may be dangerous, as
        altering elements in the list may alter the elements
        in the send queue itself. To prevent this, use the
        `deepcopy()` method.

        Returns:
            List[bytes]: A shallow copy of the send queue.
        """

        return self._send_queue.copy()

    def deepcopy(self) -> t.List[bytes]:
        """Returns a deepcopy of the send queue list

        By using this, you can modify the list without altering
        any elements of the actual send queue itself. However,
        it is more resource intensive.

        Returns:
            List[bytes]: A deep copy of the send queue.
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

        Args:
            rcv_queue (list): The list that willa ct as the receive queue.
            queue_size (int): The maximum size of the receive queue.
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

    def pushitems(self, *args: bytes) -> None:
        """Adds a list of items to the receive queue

        If the size exceeds `queue_size` when adding, then
        it will pop the front of the queue.

        A tuple (timestamp, bytes) will be added. The timestamp
        will be regenerated for each iteration of the for loop
        so they will be in order when binary searching.

        Args:
            *args (bytes): The bytes objects to add

        Raises:
            TypeError: If one of the items in *args is not a bytes object
        """

        for obj in args:
            if not isinstance(obj, bytes):
                raise TypeError("Every argument must be a bytes object")

            # add timestamp, obj to queue
            self._rcv_queue.append((time.time(), obj))

            if len(self._rcv_queue) > self._queue_size:
                # if greater than queue size, then pop first element
                self._rcv_queue.pop(0)

    def copy(self) -> t.List[t.Tuple[float, bytes]]:
        """Returns a shallow copy of the receive queue list

        The receive queue list will be a list of tuples:
        - (timestamp, bytes data)

        Using this to copy to a list may be dangerous, as
        altering elements in the list may alter the elements
        in the receive queue itself. To prevent this, use the
        `deepcopy()` method.

        Returns:
            List[Tuple[float, bytes]]: A shallow copy of the receive queue
        """

        return self._rcv_queue.copy()

    def deepcopy(self) -> t.List[t.Tuple[float, bytes]]:
        """Returns a deepcopy of the receive queue.

        The receive queue list will be a list of tuples:
        - (timestamp, bytes data)

        By using this, you can modify the list without altering
        any elements of the actual send queue itself. However,
        it is a little more resource intensive.

        Returns:
            List[Tuple[float, bytes]]: A deep copy of the receive queue
        """

        return copy.deepcopy(self._rcv_queue)
