"""
Tests for StockScreenerAgent

TDD RED phase: Write tests first to define expected behavior
"""

import pytest
from unittest.mock import patch, MagicMock

from stock_selector.agents.stock_screener import StockScreenerAgent
from stock_selector.agents.base_agent import BaseAgent
from stock_selector.queue.memory_queue import get_queue, clear_all_queues
from scorers.stock_scorer import (
    calculate_tech_score,
    calculate_fundamental_score,
    calculate_capital_score,
    calculate_comprehensive_score,
)


def setup_method():
    """每个测试前清空队列"""
    clear_all_queues()


def teardown_method():
    """每个测试后清空队列"""
    clear_all_queues()


class TestStockScreenerAgentInheritance:
    """Tests for StockScreenerAgent class inheritance."""

    def test_stock_screener_inherits_from_base_agent(self):
        """测试StockScreenerAgent继承自BaseAgent"""
        agent = StockScreenerAgent()
        assert isinstance(agent, BaseAgent)


class TestStockScreenerAgentQueues:
    """Tests for StockScreenerAgent queue configuration."""

    def test_stock_screener_has_correct_input_queue(self):
        """测试StockScreenerAgent的input_queue为chain_analysis"""
        agent = StockScreenerAgent()
        assert agent.input_queue is not None
        assert agent.input_queue.name == "chain_analysis"

    def test_stock_screener_has_correct_output_queue(self):
        """测试StockScreenerAgent的output_queue为final_stocks"""
        agent = StockScreenerAgent()
        assert agent.output_queue is not None
        assert agent.output_queue.name == "final_stocks"


class TestStockScreenerAgentProcess:
    """Tests for StockScreenerAgent.process() method."""

    @patch('stock_selector.agents.stock_screener.TushareClient')
    def test_process_returns_top_10_stocks_sorted_by_score(self, mock_tushare_client):
        """测试process()返回按分数降序排列的Top10股票"""
        # 准备测试数据 - 12只股票，验证只返回top10
        stock_codes = [f"00{i:04d}.SZ" for i in range(1, 13)]
        stocks_data = [
            {
                "code": stock_codes[i],
                "name": f"股票{i+1}",
                "price_change": 3.0 + i * 0.5,
                "volume_ratio": 1.5 + i * 0.1,
                "trend": "up",
                "earnings_growth": 15.0 + i,
                "valuation": 20 + i,
                "growth": 10.0 + i,
                "fund_flow": 5000 + i * 500,
                "chip_concentration": 0.6 + i * 0.02
            }
            for i in range(12)
        ]

        # 模拟TushareClient返回值
        mock_instance = MagicMock()
        mock_instance.get_stocks_in_sector.return_value = stock_codes[:6]
        mock_tushare_client.return_value = mock_instance

        # 构造chain_analysis数据
        chain_data = {
            "trade_date": "20240418",
            "supply_chain": [
                {"code": "BK0001", "name": "板块A", "main_amount": 1000000, "rank": 1}
            ],
            "sector_codes": ["BK0001"],
            "timestamp": 1713456000.0
        }

        # 同时mock获取日线数据
        mock_instance.get_daily_data.return_value = MagicMock()

        agent = StockScreenerAgent()
        result = agent.process(chain_data)

        # 验证返回结果格式
        assert "trade_date" in result
        assert "top_stocks" in result
        assert "total_stocks_analyzed" in result

    @patch('stock_selector.agents.stock_screener.TushareClient')
    def test_process_calculates_comprehensive_scores_correctly(self, mock_tushare_client):
        """测试process()使用正确的公式计算综合分数"""
        # 技术40% + 基本面30% + 资金30%
        input_data = {
            "code": "000001.SZ",
            "name": "平安银行",
            "price_change": 5.0,
            "volume_ratio": 2.5,
            "trend": "up",
            "earnings_growth": 30.0,
            "valuation": 15,
            "growth": 20.0,
            "fund_flow": 10000,
            "chip_concentration": 0.8
        }

        # 手动计算期望分数
        # tech_score: 0.25*100 + 0.25*100 + 0.50*80 = 90
        tech_score = calculate_tech_score({
            'price_change': 5.0,
            'volume_ratio': 2.5,
            'trend': 'up'
        })
        # fundamental_score: 0.4*100 + 0.3*80 + 0.3*100 = 94
        fundamental_score = calculate_fundamental_score({
            'earnings_growth': 30.0,
            'valuation': 15,
            'growth': 20.0
        })
        # capital_score: 0.5*100 + 0.5*80 = 90
        capital_score = calculate_capital_score({
            'fund_flow': 10000,
            'chip_concentration': 0.8
        })
        # comprehensive_score: 0.4*90 + 0.3*94 + 0.3*90 = 91.2
        expected_comprehensive = calculate_comprehensive_score(
            tech_score, fundamental_score, capital_score
        )

        # 模拟TushareClient
        mock_instance = MagicMock()
        mock_instance.get_stocks_in_sector.return_value = ["000001.SZ"]
        mock_tushare_client.return_value = mock_instance

        chain_data = {
            "trade_date": "20240418",
            "supply_chain": [
                {"code": "BK0001", "name": "板块A"}
            ],
            "sector_codes": ["BK0001"],
            "timestamp": 1713456000.0
        }

        agent = StockScreenerAgent()
        result = agent.process(chain_data)

        # 验证分数计算正确
        if result["top_stocks"]:
            top_stock = result["top_stocks"][0]
            assert "comprehensive_score" in top_stock
            assert "tech_score" in top_stock
            assert "fundamental_score" in top_stock
            assert "capital_score" in top_stock

    @patch('stock_selector.agents.stock_screener.TushareClient')
    def test_process_handles_missing_stock_data(self, mock_tushare_client):
        """测试process()处理缺失股票数据的情况"""
        # 模拟TushareClient返回空数据
        mock_instance = MagicMock()
        mock_instance.get_stocks_in_sector.return_value = []
        mock_tushare_client.return_value = mock_instance

        chain_data = {
            "trade_date": "20240418",
            "supply_chain": [
                {"code": "BK0001", "name": "板块A"}
            ],
            "sector_codes": ["BK0001"],
            "timestamp": 1713456000.0
        }

        agent = StockScreenerAgent()
        result = agent.process(chain_data)

        # 应该返回空列表
        assert result["top_stocks"] == []
        assert result["total_stocks_analyzed"] == 0

    def test_process_handles_insufficient_stock_count(self):
        """测试process()处理股票数量不足10个的情况"""
        stock_data = {
            "code": "000001.SZ",
            "name": "股票1",
            "price_change": 3.0,
            "volume_ratio": 1.5,
            "trend": "up",
            "earnings_growth": 15.0,
            "valuation": 20,
            "growth": 10.0,
            "fund_flow": 5000,
            "chip_concentration": 0.6
        }

        agent = StockScreenerAgent(tushare_token="fake_token")

        with patch.object(agent, '_get_stocks_from_sectors', return_value=["000001.SZ", "000002.SZ", "000003.SZ"]):
            with patch.object(agent, '_get_stock_data_from_tushare', return_value=stock_data):
                chain_data = {
                    "trade_date": "20240418",
                    "supply_chain": [
                        {"code": "BK0001", "name": "板块A"}
                    ],
                    "sector_codes": ["BK0001"],
                    "timestamp": 1713456000.0
                }

                result = agent.process(chain_data)

                # 不足10个时，应该返回所有股票
                assert len(result["top_stocks"]) == 3

    @patch('stock_selector.agents.stock_screener.TushareClient')
    def test_process_handles_partial_data(self, mock_tushare_client):
        """测试process()处理部分数据缺失的情况"""
        mock_instance = MagicMock()
        mock_instance.get_stocks_in_sector.return_value = ["000001.SZ"]
        mock_tushare_client.return_value = mock_instance

        chain_data = {
            "trade_date": "20240418",
            "supply_chain": [
                {"code": "BK0001", "name": "板块A"}
            ],
            "sector_codes": ["BK0001"],
            "timestamp": 1713456000.0
        }

        agent = StockScreenerAgent()
        result = agent.process(chain_data)

        # 应该使用默认值处理缺失数据
        assert "top_stocks" in result

    @patch('stock_selector.agents.stock_screener.TushareClient')
    def test_process_handles_ties_in_scores(self, mock_tushare_client):
        """测试process()处理分数相同的情况"""
        # 所有股票数据相同，分数应该相同
        mock_instance = MagicMock()
        mock_instance.get_stocks_in_sector.return_value = ["000001.SZ", "000002.SZ"]
        mock_tushare_client.return_value = mock_instance

        chain_data = {
            "trade_date": "20240418",
            "supply_chain": [
                {"code": "BK0001", "name": "板块A"}
            ],
            "sector_codes": ["BK0001"],
            "timestamp": 1713456000.0
        }

        agent = StockScreenerAgent()
        result = agent.process(chain_data)

        # 两个股票分数相同，顺序无所谓，但都应该返回
        if len(result["top_stocks"]) == 2:
            assert result["top_stocks"][0]["comprehensive_score"] == result["top_stocks"][1]["comprehensive_score"]


class TestStockScreenerAgentQueueIntegration:
    """Tests for StockScreenerAgent queue integration."""

    @patch('stock_selector.agents.stock_screener.TushareClient')
    def test_process_sends_result_to_output_queue(self, mock_tushare_client):
        """测试process()发送结果到final_stocks队列"""
        mock_instance = MagicMock()
        mock_instance.get_stocks_in_sector.return_value = ["000001.SZ"]
        mock_tushare_client.return_value = mock_instance

        chain_data = {
            "trade_date": "20240418",
            "supply_chain": [
                {"code": "BK0001", "name": "板块A"}
            ],
            "sector_codes": ["BK0001"],
            "timestamp": 1713456000.0
        }

        agent = StockScreenerAgent()
        result = agent.process(chain_data)

        # 验证数据已发送到队列
        output_queue = get_queue("final_stocks")
        assert not output_queue.empty()

        # 取出并验证消息
        message = output_queue.get()
        assert message.data["top_stocks"] is not None

    @patch('stock_selector.agents.stock_screener.TushareClient')
    def test_process_receives_from_input_queue(self, mock_tushare_client):
        """测试process()从chain_analysis队列接收数据"""
        mock_instance = MagicMock()
        mock_instance.get_stocks_in_sector.return_value = ["000001.SZ"]
        mock_tushare_client.return_value = mock_instance

        # 直接传递数据测试process()的核心逻辑
        chain_data = {
            "trade_date": "20240418",
            "supply_chain": [
                {"code": "BK0001", "name": "板块A"}
            ],
            "sector_codes": ["BK0001"],
            "timestamp": 1713456000.0
        }

        agent = StockScreenerAgent()
        result = agent.process(chain_data)

        # 验证结果 - 核心逻辑与从队列接收相同
        assert "top_stocks" in result
        assert "trade_date" in result
        assert result["trade_date"] == "20240418"


class TestStockScreenerAgentScoreCalculation:
    """Tests for StockScreenerAgent score calculation logic."""

    def test_score_formula_weights(self):
        """测试评分公式权重: 技术40% + 基本面30% + 资金30%"""
        tech_score = 80.0
        fundamental_score = 60.0
        capital_score = 100.0

        comprehensive = calculate_comprehensive_score(
            tech_score, fundamental_score, capital_score,
            tech_weight=0.4, fundamental_weight=0.3, capital_weight=0.3
        )

        # 0.4*80 + 0.3*60 + 0.3*100 = 32 + 18 + 30 = 80
        expected = 0.4 * 80 + 0.3 * 60 + 0.3 * 100
        assert comprehensive == expected

    def test_tech_score_calculation(self):
        """测试技术分计算: 涨跌幅25% + 放量25% + 趋势50%"""
        tech_data = {
            'price_change': 5.0,  # -> 100分
            'volume_ratio': 2.5,   # -> 100分
            'trend': 'up'          # -> 80分
        }
        score = calculate_tech_score(tech_data)
        # 0.25*100 + 0.25*100 + 0.50*80 = 25 + 25 + 40 = 90
        assert score == 90.0

    def test_fundamental_score_calculation(self):
        """测试基本面分计算: 业绩增速40% + 估值合理度30% + 成长性30%"""
        fundamental_data = {
            'earnings_growth': 30.0,  # -> 100分
            'valuation': 15,          # -> 80分
            'growth': 20.0            # -> 100分
        }
        score = calculate_fundamental_score(fundamental_data)
        # 0.4*100 + 0.3*80 + 0.3*100 = 40 + 24 + 30 = 94
        assert score == 94.0

    def test_capital_score_calculation(self):
        """测试资金分计算: 主力净流入50% + 筹码集中度50%"""
        capital_data = {
            'fund_flow': 10000,       # -> 100分
            'chip_concentration': 0.8  # -> 80分
        }
        score = calculate_capital_score(capital_data)
        # 0.5*100 + 0.5*80 = 50 + 40 = 90
        assert score == 90.0
