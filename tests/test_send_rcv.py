#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests if send queue and receive queue are working properly.
"""

from com_server.tools import SendQueue

SEND_LIST_TEST = [b"a\n", b"b\n", b"c\n", b"d\n"]

def test_send_queue_initializes() -> None:
    """
    Tests if the object initializes
    """

    SendQueue(SEND_LIST_TEST)

def test_send_queue_len_correct() -> None:
    """
    Tests if length of send queue is correct
    """

    sq = SendQueue(SEND_LIST_TEST)
    assert len(sq) == len(SEND_LIST_TEST)

def test_send_queue_repr_correct() -> None:
    """
    Tests that the send queue prints correctly
    """

    sq = SendQueue(SEND_LIST_TEST)
    assert repr(sq) == f"SendQueue{SEND_LIST_TEST}"

def test_front_pop() -> None:
    """
    Tests if front() and pop() are working correctly
    """

    sq = SendQueue(SEND_LIST_TEST.copy())
    assert sq.front() == SEND_LIST_TEST[0]

    sq.pop()

    assert len(sq) == len(SEND_LIST_TEST)-1 

def test_copy_deepcopy() -> None:
    """
    Tests if copy and deepcopy methods are working correctly.
    """

    sq = SendQueue(SEND_LIST_TEST.copy())
    sq_cp1 = sq.copy()
    sq_cp2 = sq.deepcopy()

    assert sq_cp1 == SEND_LIST_TEST 
    assert sq_cp2 == SEND_LIST_TEST
