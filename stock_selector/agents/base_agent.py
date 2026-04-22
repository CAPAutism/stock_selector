"""
Base agent classes for the stock selector system.

This module provides the foundational AgentMessage dataclass and BaseAgent
abstract class that all agents in the system inherit from.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

import time

from stock_selector.queue.memory_queue import MemoryQueue


@dataclass
class AgentMessage:
    """
    Message format used by agents for communication.

    Attributes:
        agent: Name of the agent that created/received this message
        data: The payload data (can be any type)
        timestamp: Auto-generated timestamp when the message was created
    """
    agent: str
    data: Any
    timestamp: float = field(default_factory=lambda: time.time())


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the stock selector system.

    Agents communicate via message queues. Each agent has:
    - An optional input queue for receiving messages
    - An optional output queue for sending messages
    - Multiple named output queues for more complex routing

    Subclasses must implement the process() method to define their behavior.
    """

    def __init__(
        self,
        name: str,
        input_queue: Optional[MemoryQueue] = None,
        output_queue: Optional[MemoryQueue] = None,
        output_queues: Optional[dict[str, MemoryQueue]] = None
    ) -> None:
        """
        Initialize the agent.

        Args:
            name: Unique name identifying this agent
            input_queue: Optional queue for receiving messages
            output_queue: Optional default queue for sending messages
            output_queues: Optional dict of named queues for routing
        """
        self.name = name
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.output_queues = output_queues or {}

    def _put_message(self, queue_name: str, data: Any) -> None:
        """
        Helper to put data into a specified queue.

        Args:
            queue_name: Name of the queue (uses output_queue if not found in output_queues)
            data: Data to put into the queue

        Raises:
            ValueError: If queue_name is not found and no default output_queue exists
        """
        if queue_name in self.output_queues:
            queue = self.output_queues[queue_name]
        elif self.output_queue is not None:
            queue = self.output_queue
        else:
            raise ValueError(f"No queue found for name: {queue_name}")

        message = AgentMessage(agent=self.name, data=data)
        queue.put(message)

    def _get_message(self, queue_name: str) -> Any:
        """
        Helper to get data from a specified queue.

        Args:
            queue_name: Name of the queue to get from (uses input_queue if 'input')

        Returns:
            The data from the queue

        Raises:
            ValueError: If queue_name is 'input' but no input_queue exists
        """
        if queue_name == 'input':
            if self.input_queue is None:
                raise ValueError("No input_queue configured")
            return self.input_queue.get()

        if queue_name in self.output_queues:
            queue = self.output_queues[queue_name]
        elif self.output_queue is not None and queue_name == '_default':
            return self.output_queue.get()
        else:
            raise ValueError(f"No queue found for name: {queue_name}")

        return queue.get()

    def send(self, data: Any, queue_name: Optional[str] = None) -> None:
        """
        Send a message to an output queue.

        Args:
            data: Data to send
            queue_name: Optional queue name. If None, uses output_queue.
                      If the queue_name is found in output_queues, uses that queue.
        """
        if queue_name is None:
            if self.output_queue is None:
                raise ValueError("No output_queue configured and no queue_name provided")
            message = AgentMessage(agent=self.name, data=data)
            self.output_queue.put(message)
        else:
            self._put_message(queue_name, data)

    def receive(self) -> AgentMessage:
        """
        Receive a message from the input queue.

        Returns:
            AgentMessage from the input queue

        Raises:
            ValueError: If no input_queue is configured
        """
        if self.input_queue is None:
            raise ValueError("No input_queue configured")

        # Get the message from queue
        message = self.input_queue.get()
        # If message is already an AgentMessage, return it directly
        if isinstance(message, AgentMessage):
            return message
        # Otherwise wrap it
        return AgentMessage(agent=self.name, data=message)

    @abstractmethod
    def process(self, data: Any) -> Any:
        """
        Process incoming data. Must be implemented by subclasses.

        Args:
            data: Data to process

        Returns:
            Processed result
        """
        ...
