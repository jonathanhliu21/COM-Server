#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests if send queue and receive queue are working properly.
"""

import pytest
from com_server.tools import SendQueue, ReceiveQueue

SEND_LIST_TEST = [b"a\n", b"b\n", b"c\n", b"d\n"]
RCV_LIST_TEST = [(0.0, b"a\n"), (0.1, b"b\n"), (0.2, b"c\n"), (0.3, b"d\n")]
TEST_QUEUE_SIZE = 32

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

def test_send_queue_front_pop() -> None:
    """
    Tests if front() and pop() are working correctly
    """

    sq = SendQueue(SEND_LIST_TEST.copy())
    assert sq.front() == SEND_LIST_TEST[0]

    sq.pop()

    assert len(sq) == len(SEND_LIST_TEST)-1 

def test_send_queue_copy_deepcopy() -> None:
    """
    Tests if copy and deepcopy methods are working correctly.
    """

    sq = SendQueue(SEND_LIST_TEST.copy())
    sq_cp1 = sq.copy()
    sq_cp2 = sq.deepcopy()

    assert sq_cp1 == SEND_LIST_TEST 
    assert sq_cp2 == SEND_LIST_TEST

def test_rcv_queue_initializes() -> None:
    """
    Test if rcv initializes
    """

    ReceiveQueue(RCV_LIST_TEST.copy(), TEST_QUEUE_SIZE)

def test_rcv_queue_len_correct() -> None:
    """
    Test if __len__ is working
    """

    rq = ReceiveQueue(RCV_LIST_TEST.copy(), TEST_QUEUE_SIZE)
    assert len(rq) == len(RCV_LIST_TEST)

def test_rcv_queue_repr_correct() -> None:
    """
    Test if __repr__ is correct
    """

    rq = ReceiveQueue(RCV_LIST_TEST.copy(), TEST_QUEUE_SIZE)
    assert repr(rq) == f"ReceiveQueue{RCV_LIST_TEST}"

def test_rcv_queue_pushitems() -> None:
    """
    Tests that items push correctly and correct exceptions get thrown
    """

    rq = ReceiveQueue(RCV_LIST_TEST.copy(), TEST_QUEUE_SIZE)
    rq.pushitems(*[b"abc"]*135)

    def _is_rcv_queue_sorted(rcv_q: list) -> bool:
        for i in range(1, len(rcv_q)):
            if (rcv_q[i][0] < rcv_q[i-1][0]):
                return False 
        
        return True
    
    assert _is_rcv_queue_sorted(rq._rcv_queue)
    assert len(rq) == TEST_QUEUE_SIZE

    with pytest.raises(TypeError):
        rq.pushitems(1, 2, 3)

def test_rcv_queue_copy_deepcopy() -> None:
    """
    Tests if copy and deepcopy methods are working correctly.
    """

    rq = ReceiveQueue(RCV_LIST_TEST.copy(), TEST_QUEUE_SIZE)
    rq_cp1 = rq.copy()
    rq_cp2 = rq.deepcopy()

    assert rq_cp1 == RCV_LIST_TEST 
    assert rq_cp2 == RCV_LIST_TEST 

def test_send_rcv_changed() -> None:
    """
    Tests that the send and receive queue change in functions
    """

    sq = SendQueue(SEND_LIST_TEST.copy())
    rcv_q = ReceiveQueue(RCV_LIST_TEST.copy(), TEST_QUEUE_SIZE)

    sq_p = sq.copy()
    rcv_q_p = rcv_q.copy()

    def custom_io_thread(sq: SendQueue, rcv_q: ReceiveQueue):
        sq.pop() 
        rcv_q.pushitems(b"4\n", b"5\n")
    
    custom_io_thread(sq, rcv_q)

    assert len(sq) == len(sq_p)-1
    assert len(rcv_q) == len(rcv_q_p) + 2
