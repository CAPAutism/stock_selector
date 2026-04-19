"""
Tests for DataCollectorAgent

TDD RED phase: Write tests first to define expected behavior
"""

import pytest
from unittest.mock import patch, MagicMock
import pandas as pd

from stock_selector.agents.data_collector import DataCollectorAgent
from stock_selector.agents.base_agent import BaseAgent
from stock_selector.queue.memory_queue import get_queue, clear_all_queues


def setup_method():
    """每个测试前清空队列"""
    clear_all_queues()


def test_data_collector_inherits_from_base_agent():
    """测试DataCollectorAgent继承自BaseAgent"""
    agent = DataCollectorAgent(token="test_token")
    assert isinstance(agent, BaseAgent)


def test_data_collector_has_correct_input_queue():
    """测试DataCollectorAgent的input_queue为None（无输入队列）"""
    agent = DataCollectorAgent(token="test_token")
    assert agent.input_queue is None


def test_data_collector_has_correct_output_queue():
    """测试DataCollectorAgent的output_queue为raw_market_data"""
    agent = DataCollectorAgent(token="test_token")
    assert agent.output_queue is not None
    assert agent.output_queue.name == "raw_market_data"


def test_data_collector_constructor_accepts_tushare_token():
    """测试DataCollectorAgent构造函数接受tushare_token参数"""
    agent = DataCollectorAgent(token="my_custom_token")
    assert agent.token == "my_custom_token"


def test_data_collector_process_returns_market_data():
    """测试DataCollectorAgent.process()返回正确格式的市场数据"""
    with patch('stock_selector.agents.data_collector.TushareClient') as mock_tushare_class:
        mock_client = MagicMock()
        mock_tushare_class.return_value = mock_client
        mock_client.get_sector_fund_flow.return_value = pd.DataFrame({
            'code': ['BK0001', 'BK0002'],
            'name': ['板块A', '板块B'],
            'close': [100.0, 200.0],
            'change': [1.5, -0.5],
            'amount': [1000000, 2000000],
            'main_amount': [500000, 300000]
        })

        agent = DataCollectorAgent(token="test_token")
        result = agent.process()

        assert 'sectors_fund_flow' in result
        assert 'sectors_heat' in result
        assert 'timestamp' in result
        assert len(result['sectors_fund_flow']) == 2


def test_data_collector_process_sends_to_queue():
    """测试DataCollectorAgent.process()发送数据到raw_market_data队列"""
    with patch('stock_selector.agents.data_collector.TushareClient') as mock_tushare_class:
        mock_client = MagicMock()
        mock_tushare_class.return_value = mock_client
        mock_client.get_sector_fund_flow.return_value = pd.DataFrame({
            'code': ['BK0001'],
            'name': ['板块A'],
            'close': [100.0],
            'change': [1.5],
            'amount': [1000000],
            'main_amount': [500000]
        })

        agent = DataCollectorAgent(token="test_token")
        result = agent.process()

        # 验证数据已发送到队列
        queue = get_queue("raw_market_data")
        assert not queue.empty()

        # 取出并验证消息
        message = queue.get()
        assert message.data['sectors_fund_flow'] is not None


def test_data_collector_handles_empty_api_response():
    """测试DataCollectorAgent处理空API响应"""
    with patch('stock_selector.agents.data_collector.TushareClient') as mock_tushare_class:
        mock_client = MagicMock()
        mock_tushare_class.return_value = mock_client
        mock_client.get_sector_fund_flow.return_value = pd.DataFrame()

        agent = DataCollectorAgent(token="test_token")
        result = agent.process()

        assert result['sectors_fund_flow'] == []
        assert result['sectors_heat'] == []


def test_data_collector_handles_api_failure():
    """测试DataCollectorAgent处理API失败"""
    with patch('stock_selector.agents.data_collector.TushareClient') as mock_tushare_class:
        mock_client = MagicMock()
        mock_tushare_class.return_value = mock_client
        mock_client.get_sector_fund_flow.side_effect = Exception("API Error")

        agent = DataCollectorAgent(token="test_token")
        result = agent.process()

        # 应该返回空数据而不是抛出异常
        assert result['sectors_fund_flow'] == []
        assert result['sectors_heat'] == []


def test_data_collector_handles_partial_data():
    """测试DataCollectorAgent处理部分数据（某些字段缺失）"""
    with patch('stock_selector.agents.data_collector.TushareClient') as mock_tushare_class:
        mock_client = MagicMock()
        mock_tushare_class.return_value = mock_client
        # DataFrame with missing columns
        mock_client.get_sector_fund_flow.return_value = pd.DataFrame({
            'code': ['BK0001'],
            'name': ['板块A']
            # missing other columns
        })

        agent = DataCollectorAgent(token="test_token")
        result = agent.process()

        assert len(result['sectors_fund_flow']) == 1
        sector = result['sectors_fund_flow'][0]
        assert sector['code'] == 'BK0001'
        assert sector['name'] == '板块A'
        # Missing fields should default to 0 or empty
        assert sector['close'] == 0
        assert sector['main_amount'] == 0


def test_data_collector_multiple_sectors_data():
    """测试DataCollectorAgent处理多个板块数据"""
    with patch('stock_selector.agents.data_collector.TushareClient') as mock_tushare_class:
        mock_client = MagicMock()
        mock_tushare_class.return_value = mock_client
        mock_client.get_sector_fund_flow.return_value = pd.DataFrame({
            'code': [f'BK{i:04d}' for i in range(10)],
            'name': [f'板块{i}' for i in range(10)],
            'close': [100.0 + i * 10 for i in range(10)],
            'change': [1.0 + i * 0.5 for i in range(10)],
            'amount': [1000000 + i * 100000 for i in range(10)],
            'main_amount': [500000 + i * 50000 for i in range(10)]
        })

        agent = DataCollectorAgent(token="test_token")
        result = agent.process()

        assert len(result['sectors_fund_flow']) == 10
        # Verify first sector has highest main_amount
        assert result['sectors_fund_flow'][0]['main_amount'] == 500000


def test_data_collector_timestamp_is_current():
    """测试DataCollectorAgent返回的时间戳是当前时间"""
    import time

    with patch('stock_selector.agents.data_collector.TushareClient') as mock_tushare_class:
        mock_client = MagicMock()
        mock_tushare_class.return_value = mock_client
        mock_client.get_sector_fund_flow.return_value = pd.DataFrame({
            'code': ['BK0001'],
            'name': ['板块A'],
            'close': [100.0],
            'change': [1.5],
            'amount': [1000000],
            'main_amount': [500000]
        })

        before_time = time.time()
        agent = DataCollectorAgent(token="test_token")
        result = agent.process()
        after_time = time.time()

        assert before_time <= result['timestamp'] <= after_time


def test_data_collector_default_token_from_settings():
    """测试DataCollectorAgent使用Settings中的默认token"""
    with patch('stock_selector.agents.data_collector.Settings') as mock_settings_class:
        mock_settings = MagicMock()
        mock_settings_class.return_value = mock_settings
        mock_settings.tushare_token = "settings_default_token"

        with patch('stock_selector.agents.data_collector.TushareClient') as mock_tushare_class:
            mock_client = MagicMock()
            mock_tushare_class.return_value = mock_client
            mock_client.get_sector_fund_flow.return_value = pd.DataFrame()

            agent = DataCollectorAgent()
            assert agent.token == "settings_default_token"
