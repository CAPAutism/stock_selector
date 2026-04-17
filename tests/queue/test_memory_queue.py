import pytest
import time
from stock_selector.queue.memory_queue import MemoryQueue, QueueEmptyError

def test_queue_put_and_get():
    """测试入队和出队"""
    q = MemoryQueue("test_queue")
    q.put({"data": "test"})
    result = q.get()
    assert result == {"data": "test"}

def test_queue_fifo():
    """测试FIFO特性"""
    q = MemoryQueue("fifo_test")
    q.put("first")
    q.put("second")
    assert q.get() == "first"
    assert q.get() == "second"

def test_queue_empty_error():
    """测试空队列抛出异常"""
    q = MemoryQueue("empty_test")
    with pytest.raises(QueueEmptyError):
        q.get(timeout=0.1)

def test_queue_size():
    """测试队列大小"""
    q = MemoryQueue("size_test")
    assert q.qsize() == 0
    q.put("item1")
    assert q.qsize() == 1
    q.put("item2")
    assert q.qsize() == 2
    q.get()
    assert q.qsize() == 1