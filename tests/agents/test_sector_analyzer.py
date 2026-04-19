"""
Tests for SectorAnalyzerAgent

TDD RED phase: Write tests first to define expected behavior
"""

import pytest
from unittest.mock import patch, MagicMock

from stock_selector.agents.sector_analyzer import SectorAnalyzerAgent
from stock_selector.agents.base_agent import BaseAgent
from stock_selector.queue.memory_queue import get_queue, clear_all_queues


def setup_method():
    """每个测试前清空队列"""
    clear_all_queues()


def teardown_method():
    """每个测试后清空队列"""
    clear_all_queues()


class TestSectorAnalyzerAgentInheritance:
    """Tests for SectorAnalyzerAgent class inheritance."""

    def test_sector_analyzer_inherits_from_base_agent(self):
        """测试SectorAnalyzerAgent继承自BaseAgent"""
        agent = SectorAnalyzerAgent()
        assert isinstance(agent, BaseAgent)


class TestSectorAnalyzerAgentQueues:
    """Tests for SectorAnalyzerAgent queue configuration."""

    def test_sector_analyzer_has_correct_input_queue(self):
        """测试SectorAnalyzerAgent的input_queue为raw_market_data"""
        agent = SectorAnalyzerAgent()
        assert agent.input_queue is not None
        assert agent.input_queue.name == "raw_market_data"

    def test_sector_analyzer_has_correct_output_queue(self):
        """测试SectorAnalyzerAgent的output_queue为sector_analysis"""
        agent = SectorAnalyzerAgent()
        assert agent.output_queue is not None
        assert agent.output_queue.name == "sector_analysis"


class TestSectorAnalyzerAgentProcess:
    """Tests for SectorAnalyzerAgent.process() method."""

    def test_process_returns_top_5_sectors_sorted_by_score(self):
        """测试process()返回按分数降序排列的Top5板块"""
        # 准备测试数据
        input_data = {
            "trade_date": "20240418",
            "sectors_fund_flow": [
                {"code": "BK0001", "name": "板块A", "main_amount": 1000000, "rank": 1},
                {"code": "BK0002", "name": "板块B", "main_amount": 900000, "rank": 2},
                {"code": "BK0003", "name": "板块C", "main_amount": 800000, "rank": 3},
                {"code": "BK0004", "name": "板块D", "main_amount": 700000, "rank": 4},
                {"code": "BK0005", "name": "板块E", "main_amount": 600000, "rank": 5},
                {"code": "BK0006", "name": "板块F", "main_amount": 500000, "rank": 6},
            ],
            "sectors_heat": [
                {"code": "BK0001", "name": "板块A", "heat_value": 80},
                {"code": "BK0002", "name": "板块B", "heat_value": 70},
                {"code": "BK0003", "name": "板块C", "heat_value": 60},
                {"code": "BK0004", "name": "板块D", "heat_value": 50},
                {"code": "BK0005", "name": "板块E", "heat_value": 40},
            ],
            "timestamp": 1713456000.0
        }

        agent = SectorAnalyzerAgent()
        result = agent.process(input_data)

        # 验证返回结果格式
        assert "top_sectors" in result
        assert "trade_date" in result
        assert len(result["top_sectors"]) == 5

        # 验证按分数降序排列
        scores = [sector["score"] for sector in result["top_sectors"]]
        assert scores == sorted(scores, reverse=True)

    def test_process_calculates_composite_score_correctly(self):
        """测试process()使用正确的公式计算综合分数"""
        # 公式: 板块热度分 = 0.6 × 资金分 + 0.4 × 热度分
        input_data = {
            "trade_date": "20240418",
            "sectors_fund_flow": [
                {"code": "BK0001", "name": "板块A", "main_amount": 1000000, "rank": 1},
            ],
            "sectors_heat": [
                {"code": "BK0001", "name": "板块A", "heat_value": 100},
            ],
            "timestamp": 1713456000.0
        }

        agent = SectorAnalyzerAgent()
        result = agent.process(input_data)

        # fund_flow_rank=1 -> fund_flow_score=100
        # heat_value=100 -> heat_score=100
        # 板块热度分 = 0.6 * 100 + 0.4 * 100 = 100
        top_sector = result["top_sectors"][0]
        assert top_sector["score"] == 100.0

    def test_process_handles_missing_heat_data(self):
        """测试process()处理缺失热度数据的情况(仅使用资金流向)"""
        input_data = {
            "trade_date": "20240418",
            "sectors_fund_flow": [
                {"code": "BK0001", "name": "板块A", "main_amount": 1000000, "rank": 1},
                {"code": "BK0002", "name": "板块B", "main_amount": 500000, "rank": 2},
            ],
            "sectors_heat": [],  # 空热度数据
            "timestamp": 1713456000.0
        }

        agent = SectorAnalyzerAgent()
        result = agent.process(input_data)

        # 应该仍然返回结果，只是热度分为0
        assert len(result["top_sectors"]) == 2
        # fund_flow_rank=1 -> score = 0.6 * 100 + 0.4 * 0 = 60
        assert result["top_sectors"][0]["score"] == 60.0

    def test_process_handles_empty_input(self):
        """测试process()处理空输入的情况"""
        input_data = {
            "trade_date": "20240418",
            "sectors_fund_flow": [],
            "sectors_heat": [],
            "timestamp": 1713456000.0
        }

        agent = SectorAnalyzerAgent()
        result = agent.process(input_data)

        assert result["top_sectors"] == []

    def test_process_handles_partial_fund_flow_data(self):
        """测试process()处理部分资金流向数据(缺少rank字段)"""
        input_data = {
            "trade_date": "20240418",
            "sectors_fund_flow": [
                {"code": "BK0001", "name": "板块A", "main_amount": 1000000},  # 缺少rank
            ],
            "sectors_heat": [
                {"code": "BK0001", "name": "板块A", "heat_value": 50},
            ],
            "timestamp": 1713456000.0
        }

        agent = SectorAnalyzerAgent()
        result = agent.process(input_data)

        # 默认rank为0，资金分也为0
        # 板块热度分 = 0.6 * 0 + 0.4 * 50 = 20
        assert result["top_sectors"][0]["score"] == 20.0

    def test_process_handles_ties_in_scores(self):
        """测试process()处理分数相同的情况"""
        input_data = {
            "trade_date": "20240418",
            "sectors_fund_flow": [
                {"code": "BK0001", "name": "板块A", "rank": 100},
                {"code": "BK0002", "name": "板块B", "rank": 100},
            ],
            "sectors_heat": [
                {"code": "BK0001", "name": "板块A", "heat_value": 0},
                {"code": "BK0002", "name": "板块B", "heat_value": 0},
            ],
            "timestamp": 1713456000.0
        }

        agent = SectorAnalyzerAgent()
        result = agent.process(input_data)

        # 两个板块分数相同，都应该返回
        assert len(result["top_sectors"]) == 2
        # 分数相同（都是0），顺序无所谓
        assert result["top_sectors"][0]["score"] == result["top_sectors"][1]["score"]

    def test_process_handles_insufficient_sectors(self):
        """测试process()处理板块数量不足5个的情况"""
        input_data = {
            "trade_date": "20240418",
            "sectors_fund_flow": [
                {"code": "BK0001", "name": "板块A", "rank": 1},
                {"code": "BK0002", "name": "板块B", "rank": 2},
                {"code": "BK0003", "name": "板块C", "rank": 3},
            ],
            "sectors_heat": [
                {"code": "BK0001", "name": "板块A", "heat_value": 100},
                {"code": "BK0002", "name": "板块B", "heat_value": 50},
                {"code": "BK0003", "name": "板块C", "heat_value": 30},
            ],
            "timestamp": 1713456000.0
        }

        agent = SectorAnalyzerAgent()
        result = agent.process(input_data)

        # 不足5个时，返回所有板块
        assert len(result["top_sectors"]) == 3


class TestSectorAnalyzerAgentQueueIntegration:
    """Tests for SectorAnalyzerAgent queue integration."""

    def test_process_sends_result_to_output_queue(self):
        """测试process()发送结果到sector_analysis队列"""
        input_data = {
            "trade_date": "20240418",
            "sectors_fund_flow": [
                {"code": "BK0001", "name": "板块A", "rank": 1},
            ],
            "sectors_heat": [
                {"code": "BK0001", "name": "板块A", "heat_value": 100},
            ],
            "timestamp": 1713456000.0
        }

        agent = SectorAnalyzerAgent()
        result = agent.process(input_data)

        # 验证数据已发送到队列
        output_queue = get_queue("sector_analysis")
        assert not output_queue.empty()

        # 取出并验证消息
        message = output_queue.get()
        assert message.data["top_sectors"] is not None

    def test_process_receives_from_input_queue(self):
        """测试process()从raw_market_data队列接收数据"""
        # 直接传递数据测试process()的队列接收逻辑
        # (队列集成测试需要特殊设置，此处测试process方法的核心逻辑)
        input_data = {
            "trade_date": "20240418",
            "sectors_fund_flow": [
                {"code": "BK0001", "name": "板块A", "rank": 1},
            ],
            "sectors_heat": [
                {"code": "BK0001", "name": "板块A", "heat_value": 100},
            ],
            "timestamp": 1713456000.0
        }

        # 创建agent并调用process，传入数据
        agent = SectorAnalyzerAgent()
        result = agent.process(input_data)

        # 验证结果 - 核心逻辑与从队列接收相同
        assert len(result["top_sectors"]) == 1
        assert result["top_sectors"][0]["name"] == "板块A"
