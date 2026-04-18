"""
Tests for BaseAgent and AgentMessage

TDD RED phase - These tests define the expected behavior.
"""
import pytest
import time
from abc import ABC
from typing import Any

# Import the modules under test
from stock_selector.agents.base_agent import AgentMessage, BaseAgent


class TestAgentMessage:
    """Tests for AgentMessage dataclass"""

    def test_agent_message_has_agent_field(self):
        """AgentMessage should have agent name field"""
        msg = AgentMessage(agent="test_agent", data={"value": 123})
        assert msg.agent == "test_agent"

    def test_agent_message_has_data_field(self):
        """AgentMessage should have data field"""
        msg = AgentMessage(agent="test_agent", data={"value": 123})
        assert msg.data == {"value": 123}

    def test_agent_message_has_timestamp_field(self):
        """AgentMessage should have timestamp field"""
        before = time.time()
        msg = AgentMessage(agent="test_agent", data={"value": 123})
        after = time.time()
        assert isinstance(msg.timestamp, float)
        assert before <= msg.timestamp <= after

    def test_agent_message_timestamp_auto_generated(self):
        """AgentMessage timestamp should be auto-generated"""
        msg1 = AgentMessage(agent="agent1", data="data1")
        time.sleep(0.01)  # Small delay to ensure different timestamp
        msg2 = AgentMessage(agent="agent2", data="data2")
        # msg2.timestamp should be >= msg1.timestamp (accounting for sleep)
        assert msg2.timestamp >= msg1.timestamp

    def test_agent_message_with_empty_data(self):
        """AgentMessage should handle empty data"""
        msg = AgentMessage(agent="test_agent", data=None)
        assert msg.agent == "test_agent"
        assert msg.data is None


class TestBaseAgentAbstract:
    """Tests for BaseAgent abstract class behavior"""

    def test_base_agent_cannot_be_instantiated_directly(self):
        """BaseAgent is abstract and cannot be instantiated directly"""
        # BaseAgent with abstract methods cannot be instantiated
        with pytest.raises(TypeError):
            BaseAgent(name="test_agent")

    def test_base_agent_is_abc(self):
        """BaseAgent should be an ABC"""
        assert issubclass(BaseAgent, ABC)

    def test_base_agent_has_process_abstract_method(self):
        """BaseAgent.process should be abstract"""
        # This test verifies the abstract method exists
        assert getattr(BaseAgent, 'process', None) is not None


class TestBaseAgentSend:
    """Tests for BaseAgent.send() method"""

    def test_send_method_exists(self):
        """BaseAgent should have send method"""
        # Create a concrete subclass to test
        class ConcreteAgent(BaseAgent):
            def process(self, data: Any) -> Any:
                return data

        agent = ConcreteAgent(name="test_agent")
        assert hasattr(agent, 'send')

    def test_send_puts_message_to_output_queue(self):
        """send() should put message into output_queue"""
        from stock_selector.queue.memory_queue import MemoryQueue

        class ConcreteAgent(BaseAgent):
            def process(self, data: Any) -> Any:
                return data

        output_queue = MemoryQueue("output")
        agent = ConcreteAgent(
            name="test_agent",
            output_queue=output_queue
        )
        agent.send({"message": "hello"})

        assert output_queue.qsize() == 1
        msg = output_queue.get()
        assert msg.agent == "test_agent"
        assert msg.data == {"message": "hello"}


class TestBaseAgentReceive:
    """Tests for BaseAgent.receive() method"""

    def test_receive_method_exists(self):
        """BaseAgent should have receive method"""
        class ConcreteAgent(BaseAgent):
            def process(self, data: Any) -> Any:
                return data

        agent = ConcreteAgent(name="test_agent")
        assert hasattr(agent, 'receive')

    def test_receive_gets_message_from_input_queue(self):
        """receive() should get message from input_queue"""
        from stock_selector.queue.memory_queue import MemoryQueue

        class ConcreteAgent(BaseAgent):
            def process(self, data: Any) -> Any:
                return data

        input_queue = MemoryQueue("input")
        input_queue.put({"message": "world"})

        agent = ConcreteAgent(
            name="test_agent",
            input_queue=input_queue
        )
        msg = agent.receive()

        assert msg.data == {"message": "world"}

    def test_receive_returns_agent_message(self):
        """receive() should return AgentMessage"""
        from stock_selector.queue.memory_queue import MemoryQueue

        class ConcreteAgent(BaseAgent):
            def process(self, data: Any) -> Any:
                return data

        input_queue = MemoryQueue("input")
        input_queue.put({"data": "test"})

        agent = ConcreteAgent(
            name="test_agent",
            input_queue=input_queue
        )
        msg = agent.receive()

        assert isinstance(msg, AgentMessage)
        assert msg.agent == "test_agent"


class TestBaseAgentConstructor:
    """Tests for BaseAgent.__init__() method"""

    def test_constructor_accepts_name(self):
        """Constructor should accept name parameter"""
        class ConcreteAgent(BaseAgent):
            def process(self, data: Any) -> Any:
                return data

        agent = ConcreteAgent(name="my_agent")
        assert agent.name == "my_agent"

    def test_constructor_accepts_input_queue(self):
        """Constructor should accept input_queue parameter"""
        from stock_selector.queue.memory_queue import MemoryQueue

        class ConcreteAgent(BaseAgent):
            def process(self, data: Any) -> Any:
                return data

        input_queue = MemoryQueue("test_input")
        agent = ConcreteAgent(
            name="test_agent",
            input_queue=input_queue
        )
        assert agent.input_queue is input_queue

    def test_constructor_accepts_output_queue(self):
        """Constructor should accept output_queue parameter"""
        from stock_selector.queue.memory_queue import MemoryQueue

        class ConcreteAgent(BaseAgent):
            def process(self, data: Any) -> Any:
                return data

        output_queue = MemoryQueue("test_output")
        agent = ConcreteAgent(
            name="test_agent",
            output_queue=output_queue
        )
        assert agent.output_queue is output_queue

    def test_constructor_accepts_output_queues(self):
        """Constructor should accept output_queues parameter"""
        from stock_selector.queue.memory_queue import MemoryQueue

        class ConcreteAgent(BaseAgent):
            def process(self, data: Any) -> Any:
                return data

        queues = {
            "queue1": MemoryQueue("output1"),
            "queue2": MemoryQueue("output2")
        }
        agent = ConcreteAgent(
            name="test_agent",
            output_queues=queues
        )
        assert agent.output_queues is queues


class TestConcreteSubclass:
    """Tests for concrete BaseAgent subclasses"""

    def test_concrete_subclass_can_be_instantiated(self):
        """Concrete subclass can be instantiated"""
        class MyAgent(BaseAgent):
            def process(self, data: Any) -> Any:
                return data

        agent = MyAgent(name="my_agent")
        assert agent.name == "my_agent"

    def test_process_method_is_called(self):
        """process() should be called when agent processes data"""
        from stock_selector.queue.memory_queue import MemoryQueue

        class MyAgent(BaseAgent):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.processed_data = None

            def process(self, data: Any) -> Any:
                self.processed_data = data
                return f"processed: {data}"

        input_queue = MemoryQueue("input")
        output_queue = MemoryQueue("output")
        input_queue.put({"raw": "data"})

        agent = MyAgent(
            name="processor",
            input_queue=input_queue,
            output_queue=output_queue
        )

        # Get message from input queue and process it
        msg = agent.receive()
        result = agent.process(msg.data)

        assert agent.processed_data == {"raw": "data"}
        assert result == "processed: {'raw': 'data'}"

    def test_send_to_named_queue(self):
        """send() should support sending to named queues in output_queues"""
        from stock_selector.queue.memory_queue import MemoryQueue

        class MyAgent(BaseAgent):
            def process(self, data: Any) -> Any:
                return data

        queue1 = MemoryQueue("named_queue1")
        queue2 = MemoryQueue("named_queue2")
        output_queues = {"q1": queue1, "q2": queue2}

        agent = MyAgent(
            name="multi_queue_agent",
            output_queues=output_queues
        )

        agent.send({"to": "q1"}, queue_name="q1")
        agent.send({"to": "q2"}, queue_name="q2")

        assert queue1.qsize() == 1
        assert queue2.qsize() == 1

        msg1 = queue1.get()
        msg2 = queue2.get()
        assert msg1.data == {"to": "q1"}
        assert msg2.data == {"to": "q2"}
