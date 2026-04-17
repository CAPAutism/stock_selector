import queue
import threading
from typing import Any, Optional
from dataclasses import dataclass, field

class QueueEmptyError(Exception):
    """队列为空异常"""
    pass

@dataclass
class QueueMessage:
    """队列消息封装"""
    data: Any
    timestamp: float = field(default_factory=lambda: __import__('time').time())

class MemoryQueue:
    """
    内存消息队列实现

    线程安全，支持多生产者多消费者模式
    """

    def __init__(self, name: str, maxsize: int = 0):
        """
        初始化队列

        Args:
            name: 队列名称
            maxsize: 队列最大容量，0表示无限制
        """
        self.name = name
        self._queue: queue.Queue = queue.Queue(maxsize=maxsize)
        self._lock = threading.Lock()

    def put(self, data: Any, block: bool = True, timeout: Optional[float] = None) -> None:
        """
        入队

        Args:
            data: 消息数据
            block: 是否阻塞
            timeout: 超时时间
        """
        message = QueueMessage(data=data)
        self._queue.put(message, block=block, timeout=timeout)

    def get(self, block: bool = True, timeout: Optional[float] = None) -> Any:
        """
        出队

        Args:
            block: 是否阻塞
            timeout: 超时时间

        Returns:
            消息数据

        Raises:
            QueueEmptyError: 队列为空
        """
        try:
            message = self._queue.get(block=block, timeout=timeout)
            return message.data
        except queue.Empty:
            raise QueueEmptyError(f"Queue '{self.name}' is empty")

    def qsize(self) -> int:
        """返回队列大小"""
        return self._queue.qsize()

    def empty(self) -> bool:
        """判断队列是否为空"""
        return self._queue.empty()

    def clear(self) -> None:
        """清空队列"""
        with self._lock:
            while not self._queue.empty():
                try:
                    self._queue.get_nowait()
                except queue.Empty:
                    break

# 全局队列注册表
_queues: dict[str, MemoryQueue] = {}

def get_queue(name: str, maxsize: int = 0) -> MemoryQueue:
    """
    获取或创建命名队列

    Args:
        name: 队列名称
        maxsize: 队列最大容量

    Returns:
        MemoryQueue实例
    """
    if name not in _queues:
        _queues[name] = MemoryQueue(name, maxsize)
    return _queues[name]

def clear_all_queues() -> None:
    """清空所有队列"""
    global _queues
    for q in _queues.values():
        q.clear()
    _queues.clear()
