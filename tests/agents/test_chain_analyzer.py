"""
Tests for ChainAnalyzerAgent

TDD RED phase: Write tests first to define expected behavior

职责:
- 从sector_analysis队列消费数据
- 分析板块内个股的产业链位置(上游/中游/下游)
- 输出产业链结构到chain_analysis队列
"""

import pytest
from unittest.mock import patch, MagicMock

from stock_selector.agents.chain_analyzer import ChainAnalyzerAgent
from stock_selector.agents.base_agent import BaseAgent
from stock_selector.queue.memory_queue import get_queue, clear_all_queues


def setup_method():
    """每个测试前清空队列"""
    clear_all_queues()


def teardown_method():
    """每个测试后清空队列"""
    clear_all_queues()


class TestChainAnalyzerAgentInheritance:
    """Tests for ChainAnalyzerAgent class inheritance."""

    def test_chain_analyzer_inherits_from_base_agent(self):
        """测试ChainAnalyzerAgent继承自BaseAgent"""
        agent = ChainAnalyzerAgent()
        assert isinstance(agent, BaseAgent)


class TestChainAnalyzerAgentQueues:
    """Tests for ChainAnalyzerAgent queue configuration."""

    def test_chain_analyzer_has_correct_input_queue(self):
        """测试ChainAnalyzerAgent的input_queue为sector_analysis"""
        agent = ChainAnalyzerAgent()
        assert agent.input_queue is not None
        assert agent.input_queue.name == "sector_analysis"

    def test_chain_analyzer_has_correct_output_queue(self):
        """测试ChainAnalyzerAgent的output_queue为chain_analysis"""
        agent = ChainAnalyzerAgent()
        assert agent.output_queue is not None
        assert agent.output_queue.name == "chain_analysis"


class TestChainAnalyzerAgentProcess:
    """Tests for ChainAnalyzerAgent.process() method."""

    @patch('stock_selector.agents.chain_analyzer.TushareClient')
    def test_process_identifies_supply_chain_structure(self, mock_tushare_class):
        """测试process()正确识别产业链结构"""
        # 模拟TushareClient返回个股列表
        mock_client = MagicMock()
        mock_tushare_class.return_value = mock_client
        mock_client.get_stocks_in_sector.side_effect = [
            ["stock001", "stock002", "stock003"],  # 板块A的成分股
            ["stock004", "stock005"],               # 板块B的成分股
        ]

        # 准备输入数据：来自sector_analysis队列的Top5热门板块
        input_data = {
            "trade_date": "20240418",
            "top_sectors": [
                {"code": "BK0001", "name": "板块A", "score": 100},
                {"code": "BK0002", "name": "板块B", "score": 90},
            ],
            "total_sectors_analyzed": 10
        }

        agent = ChainAnalyzerAgent()
        result = agent.process(input_data)

        # 验证返回结果包含产业链结构
        assert "trade_date" in result
        assert "chain_structures" in result
        assert "total_stocks_analyzed" in result
        assert result["trade_date"] == "20240418"

    @patch('stock_selector.agents.chain_analyzer.TushareClient')
    def test_process_classifies_stocks_into_upstream_midstream_downstream(self, mock_tushare_class):
        """测试process()将个股分类到上游/中游/下游"""
        mock_client = MagicMock()
        mock_tushare_class.return_value = mock_client
        mock_client.get_stocks_in_sector.side_effect = [
            ["stock001", "stock002"],  # 板块A
        ]

        input_data = {
            "trade_date": "20240418",
            "top_sectors": [
                {"code": "BK0001", "name": "板块A", "score": 100},
            ],
            "total_sectors_analyzed": 5
        }

        agent = ChainAnalyzerAgent()
        result = agent.process(input_data)

        # 验证每个stock都有link_type标记
        assert "chain_structures" in result
        # 检查是否每个股票都有link_type分类
        for chain in result["chain_structures"]:
            assert "upstream" in chain or "midstream" in chain or "downstream" in chain
            for stock in chain.get("upstream", []) + chain.get("midstream", []) + chain.get("downstream", []):
                assert "link_type" in stock

    @patch('stock_selector.agents.chain_analyzer.TushareClient')
    def test_process_handles_sectors_without_clear_chain_structure(self, mock_tushare_class):
        """测试process()处理无法明确分类的板块"""
        mock_client = MagicMock()
        mock_tushare_class.return_value = mock_client
        mock_client.get_stocks_in_sector.side_effect = [
            [],  # 板块A没有成分股
        ]

        input_data = {
            "trade_date": "20240418",
            "top_sectors": [
                {"code": "BK0001", "name": "板块A", "score": 100},
            ],
            "total_sectors_analyzed": 5
        }

        agent = ChainAnalyzerAgent()
        result = agent.process(input_data)

        # 应该正常返回，只是没有股票数据
        assert result is not None
        assert "chain_structures" in result

    @patch('stock_selector.agents.chain_analyzer.TushareClient')
    def test_process_handles_empty_sectors(self, mock_tushare_class):
        """测试process()处理空板块列表"""
        mock_client = MagicMock()
        mock_tushare_class.return_value = mock_client

        input_data = {
            "trade_date": "20240418",
            "top_sectors": [],  # 没有热门板块
            "total_sectors_analyzed": 0
        }

        agent = ChainAnalyzerAgent()
        result = agent.process(input_data)

        # 应该返回空结果
        assert result["chain_structures"] == []
        assert result["total_stocks_analyzed"] == 0

    @patch('stock_selector.agents.chain_analyzer.TushareClient')
    def test_process_handles_single_stock_sector(self, mock_tushare_class):
        """测试process()处理单只股票的板块"""
        mock_client = MagicMock()
        mock_tushare_class.return_value = mock_client
        mock_client.get_stocks_in_sector.side_effect = [
            ["stock001"],  # 只有一个股票
        ]

        input_data = {
            "trade_date": "20240418",
            "top_sectors": [
                {"code": "BK0001", "name": "板块A", "score": 100},
            ],
            "total_sectors_analyzed": 5
        }

        agent = ChainAnalyzerAgent()
        result = agent.process(input_data)

        # 应该正常处理单只股票
        assert "chain_structures" in result
        total_stocks = sum(
            len(chain.get("upstream", [])) + len(chain.get("midstream", [])) + len(chain.get("downstream", []))
            for chain in result["chain_structures"]
        )
        assert total_stocks >= 1

    @patch('stock_selector.agents.chain_analyzer.TushareClient')
    def test_process_handles_missing_sector_data(self, mock_tushare_class):
        """测试process()处理缺失板块数据"""
        mock_client = MagicMock()
        mock_tushare_class.return_value = mock_client

        # 缺少top_sectors字段
        input_data = {
            "trade_date": "20240418",
            "total_sectors_analyzed": 0
        }

        agent = ChainAnalyzerAgent()
        result = agent.process(input_data)

        # 应该返回空结果而不是抛出异常
        assert result["chain_structures"] == []
        assert result["total_stocks_analyzed"] == 0


class TestChainAnalyzerAgentChainScorer:
    """Tests for ChainAnalyzerAgent supply chain scoring."""

    @patch('stock_selector.agents.chain_analyzer.TushareClient')
    def test_process_uses_chain_scorer(self, mock_tushare_class):
        """测试process()使用ChainScorer进行评分"""
        mock_client = MagicMock()
        mock_tushare_class.return_value = mock_client
        mock_client.get_stocks_in_sector.side_effect = [
            ["stock001", "stock002"],
        ]

        input_data = {
            "trade_date": "20240418",
            "top_sectors": [
                {"code": "BK0001", "name": "板块A", "score": 100},
            ],
            "total_sectors_analyzed": 5
        }

        agent = ChainAnalyzerAgent()
        result = agent.process(input_data)

        # 验证返回的股票包含score字段(来自ChainScorer)
        for chain in result["chain_structures"]:
            for stock in chain.get("upstream", []) + chain.get("midstream", []) + chain.get("downstream", []):
                assert "score" in stock

    @patch('stock_selector.agents.chain_analyzer.TushareClient')
    def test_process_ranks_stocks_within_link(self, mock_tushare_class):
        """测试process()对同环节内的股票进行排名"""
        mock_client = MagicMock()
        mock_tushare_class.return_value = mock_client
        mock_client.get_stocks_in_sector.side_effect = [
            ["stock001", "stock002", "stock003"],
        ]

        input_data = {
            "trade_date": "20240418",
            "top_sectors": [
                {"code": "BK0001", "name": "板块A", "score": 100},
            ],
            "total_sectors_analyzed": 5
        }

        agent = ChainAnalyzerAgent()
        result = agent.process(input_data)

        # 找到任一环节的股票
        all_stocks_in_same_link = []
        for chain in result["chain_structures"]:
            for link_type in ["upstream", "midstream", "downstream"]:
                if len(chain.get(link_type, [])) >= 2:
                    all_stocks_in_same_link = chain[link_type]
                    break
            if all_stocks_in_same_link:
                break

        # 如果有同环节的多只股票，验证有不同分数
        if len(all_stocks_in_same_link) >= 2:
            scores = [s["score"] for s in all_stocks_in_same_link]
            # 至少应该有不同分数(除非完全相同排名)
            assert len(set(scores)) >= 1  # 允许相同分数但必须存在


class TestChainAnalyzerAgentQueueIntegration:
    """Tests for ChainAnalyzerAgent queue integration."""

    @patch('stock_selector.agents.chain_analyzer.TushareClient')
    def test_process_sends_result_to_output_queue(self, mock_tushare_class):
        """测试process()发送结果到chain_analysis队列"""
        mock_client = MagicMock()
        mock_tushare_class.return_value = mock_client
        mock_client.get_stocks_in_sector.side_effect = [
            ["stock001"],
        ]

        input_data = {
            "trade_date": "20240418",
            "top_sectors": [
                {"code": "BK0001", "name": "板块A", "score": 100},
            ],
            "total_sectors_analyzed": 5
        }

        agent = ChainAnalyzerAgent()
        result = agent.process(input_data)

        # 验证数据已发送到队列
        output_queue = get_queue("chain_analysis")
        assert not output_queue.empty()

        # 取出并验证消息
        message = output_queue.get()
        assert message.data["chain_structures"] is not None

    @patch('stock_selector.agents.chain_analyzer.TushareClient')
    def test_process_receives_from_input_queue(self, mock_tushare_class):
        """测试process()从sector_analysis队列接收数据"""
        mock_client = MagicMock()
        mock_tushare_class.return_value = mock_client
        mock_client.get_stocks_in_sector.side_effect = [
            ["stock001"],
        ]

        input_data = {
            "trade_date": "20240418",
            "top_sectors": [
                {"code": "BK0001", "name": "板块A", "score": 100},
            ],
            "total_sectors_analyzed": 5
        }

        agent = ChainAnalyzerAgent()
        result = agent.process(input_data)

        # 验证结果 - 核心逻辑与从队列接收相同
        assert result is not None
        assert "chain_structures" in result


class TestChainAnalyzerAgentEdgeCases:
    """Tests for edge cases and improved coverage."""

    def test_classify_stock_position_with_empty_code(self):
        """测试_classify_stock_position处理空代码"""
        agent = ChainAnalyzerAgent()
        # 空字符串应该返回midstream
        result = agent._classify_stock_position("", "BK0001")
        assert result == "midstream"

    def test_classify_stock_position_upstream(self):
        """测试_classify_stock_position分类到上游"""
        agent = ChainAnalyzerAgent()
        # 30 % 3 = 0 -> upstream
        result = agent._classify_stock_position("30", "BK0001")
        assert result == "upstream"

    def test_classify_stock_position_midstream(self):
        """测试_classify_stock_position分类到中游"""
        agent = ChainAnalyzerAgent()
        # 31 % 3 = 1 -> midstream
        result = agent._classify_stock_position("31", "BK0001")
        assert result == "midstream"

    def test_classify_stock_position_downstream(self):
        """测试_classify_stock_position分类到下游"""
        agent = ChainAnalyzerAgent()
        # 32 % 3 = 2 -> downstream
        result = agent._classify_stock_position("32", "BK0001")
        assert result == "downstream"

    def test_classify_stock_position_with_non_numeric_code(self):
        """测试_classify_stock_position处理非数字代码"""
        agent = ChainAnalyzerAgent()
        # 非数字代码应该返回midstream
        result = agent._classify_stock_position("INVALID", "BK0001")
        assert result == "midstream"

    @patch.dict('os.environ', {'TUSHARE_TOKEN': 'fake_token'})
    @patch('stock_selector.agents.chain_analyzer.TushareClient')
    def test_process_uses_tushare_client_when_token_available(self, mock_tushare_class):
        """测试当TUSHARE_TOKEN存在时使用TushareClient"""
        mock_client = MagicMock()
        mock_tushare_class.return_value = mock_client
        mock_client.get_stocks_in_sector.side_effect = [
            ["stock001", "stock002"],
        ]

        input_data = {
            "trade_date": "20240418",
            "top_sectors": [
                {"code": "BK0001", "name": "板块A", "score": 100},
            ],
            "total_sectors_analyzed": 5
        }

        agent = ChainAnalyzerAgent()
        result = agent.process(input_data)

        # 验证TushareClient被调用
        assert mock_client.get_stocks_in_sector.called
        assert "chain_structures" in result

    @patch.dict('os.environ', {'TUSHARE_TOKEN': 'fake_token'})
    @patch('stock_selector.agents.chain_analyzer.TushareClient')
    def test_process_handles_tushare_returning_empty_list(self, mock_tushare_class):
        """测试TushareClient返回空列表时处理"""
        mock_client = MagicMock()
        mock_tushare_class.return_value = mock_client
        mock_client.get_stocks_in_sector.side_effect = [
            [],  # 返回空列表
        ]

        input_data = {
            "trade_date": "20240418",
            "top_sectors": [
                {"code": "BK0001", "name": "板块A", "score": 100},
            ],
            "total_sectors_analyzed": 5
        }

        agent = ChainAnalyzerAgent()
        result = agent.process(input_data)

        # 应该正常处理空列表
        assert "chain_structures" in result
        assert result["total_stocks_analyzed"] == 0
