"""
Tests for ObsidianReportAgent

TDD RED phase: Write tests first to define expected behavior
"""

import os
import pytest
import tempfile
import shutil
from datetime import datetime
from unittest.mock import patch, MagicMock

from stock_selector.agents.obsidian_report import ObsidianReportAgent
from stock_selector.agents.base_agent import BaseAgent
from stock_selector.queue.memory_queue import get_queue, clear_all_queues


def setup_method():
    """每个测试前清空队列"""
    clear_all_queues()


def teardown_method():
    """每个测试后清空队列"""
    clear_all_queues()


class TestObsidianReportAgentInheritance:
    """Tests for ObsidianReportAgent class inheritance."""

    def test_obsidian_report_inherits_from_base_agent(self):
        """测试ObsidianReportAgent继承自BaseAgent"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = ObsidianReportAgent(obsidian_path=tmpdir)
            assert isinstance(agent, BaseAgent)


class TestObsidianReportAgentQueues:
    """Tests for ObsidianReportAgent queue configuration."""

    def test_obsidian_report_has_correct_input_queue(self):
        """测试ObsidianReportAgent的input_queue为final_stocks"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = ObsidianReportAgent(obsidian_path=tmpdir)
            assert agent.input_queue is not None
            assert agent.input_queue.name == "final_stocks"

    def test_obsidian_report_has_no_output_queue(self):
        """测试ObsidianReportAgent的output_queue为None（文件输出）"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = ObsidianReportAgent(obsidian_path=tmpdir)
            assert agent.output_queue is None


class TestObsidianReportAgentProcess:
    """Tests for ObsidianReportAgent.process() method."""

    def test_process_generates_markdown_report(self):
        """测试process()生成正确格式的Markdown报告"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = ObsidianReportAgent(obsidian_path=tmpdir)

            # 准备完整的测试数据
            test_data = {
                "trade_date": "20240418",
                "top_stocks": [
                    {
                        "rank": 1,
                        "code": "000001.SZ",
                        "name": "平安银行",
                        "comprehensive_score": 85.5,
                        "tech_signal": "突破",
                        "money_signal": "净流入",
                        "core_logic": "估值修复+业绩增长"
                    },
                    {
                        "rank": 2,
                        "code": "000002.SZ",
                        "name": "万科A",
                        "comprehensive_score": 82.3,
                        "tech_signal": "趋势向上",
                        "money_signal": "资金流入",
                        "core_logic": "政策利好+超跌反弹"
                    }
                ],
                "sectors": [
                    {
                        "rank": 1,
                        "name": "银行板块",
                        "fund_heat": 85.0,
                        "internet_heat": 75.0,
                        "total_score": 81.0,
                        "logic": "低估值+稳业绩"
                    },
                    {
                        "rank": 2,
                        "name": "房地产板块",
                        "fund_heat": 78.0,
                        "internet_heat": 80.0,
                        "total_score": 78.8,
                        "logic": "政策宽松+销售回暖"
                    }
                ],
                "supply_chains": [
                    {
                        "sector_name": "银行板块",
                        "upstream": {"name": "招商银行", "code": "600036.SH", "position": "关键资源"},
                        "midstream": {"name": "平安银行", "code": "000001.SZ", "position": "核心制造"},
                        "downstream": {"name": "万科A", "code": "000002.SZ", "position": "终端应用"}
                    }
                ],
                "industry_distribution": {
                    "upstream": {"count": 3, "stocks": ["招商银行", "浦发银行", "兴业银行"]},
                    "midstream": {"count": 5, "stocks": ["平安银行", "宁波银行", "工商银行"]},
                    "downstream": {"count": 2, "stocks": ["万科A", "保利发展"]}
                },
                "data_sources": {
                    "fund_flow": {"source": "Tushare", "update_time": "2024-04-18 16:00"},
                    "internet_heat": {"source": "雪球", "update_time": "2024-04-18 15:30"},
                    "stock_price": {"source": "Tushare", "update_time": "2024-04-18 16:00"}
                }
            }

            result = agent.process(test_data)

            # 验证返回结果
            assert result["success"] is True
            assert "report_path" in result
            assert "trade_date" in result

    def test_process_writes_to_correct_file_path(self):
        """测试process()写入正确的文件路径 选股报告/YYYY-MM-DD.md"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = ObsidianReportAgent(obsidian_path=tmpdir)

            test_data = {
                "trade_date": "20240418",
                "top_stocks": [
                    {
                        "rank": 1,
                        "code": "000001.SZ",
                        "name": "平安银行",
                        "comprehensive_score": 85.5,
                        "tech_signal": "突破",
                        "money_signal": "净流入",
                        "core_logic": "估值修复"
                    }
                ],
                "sectors": [],
                "supply_chains": [],
                "industry_distribution": {"upstream": {}, "midstream": {}, "downstream": {}},
                "data_sources": {}
            }

            result = agent.process(test_data)

            # 验证文件路径格式
            expected_dir = os.path.join(tmpdir, "选股报告")
            expected_file = os.path.join(expected_dir, "2024-04-18.md")

            assert os.path.exists(expected_file)
            assert result["report_path"] == expected_file

    def test_process_creates_report_directory_if_not_exists(self):
        """测试process()在报告目录不存在时创建它"""
        with tempfile.TemporaryDirectory() as tmpdir:
            obsidian_path = os.path.join(tmpdir, "vault")
            agent = ObsidianReportAgent(obsidian_path=obsidian_path)

            test_data = {
                "trade_date": "20240418",
                "top_stocks": [],
                "sectors": [],
                "supply_chains": [],
                "industry_distribution": {"upstream": {}, "midstream": {}, "downstream": {}},
                "data_sources": {}
            }

            # 验证目录不存在
            report_dir = os.path.join(obsidian_path, "选股报告")
            assert not os.path.exists(report_dir)

            result = agent.process(test_data)

            # 验证目录已创建
            assert os.path.exists(report_dir)
            assert os.path.isdir(report_dir)

    def test_process_handles_empty_stocks(self):
        """测试process()处理空股票列表的情况"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = ObsidianReportAgent(obsidian_path=tmpdir)

            test_data = {
                "trade_date": "20240418",
                "top_stocks": [],
                "sectors": [],
                "supply_chains": [],
                "industry_distribution": {"upstream": {}, "midstream": {}, "downstream": {}},
                "data_sources": {}
            }

            result = agent.process(test_data)

            # 应该仍然生成报告，只是内容为空
            assert result["success"] is True
            assert os.path.exists(result["report_path"])

    def test_process_handles_partial_data(self):
        """测试process()处理部分数据缺失的情况"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = ObsidianReportAgent(obsidian_path=tmpdir)

            # 只有必填字段的部分数据
            test_data = {
                "trade_date": "20240418",
                "top_stocks": [
                    {"code": "000001.SZ", "name": "测试股票"}
                ]
            }

            result = agent.process(test_data)

            # 应该优雅处理缺失数据
            assert result["success"] is True
            assert os.path.exists(result["report_path"])

    def test_process_handles_missing_sectors(self):
        """测试process()处理缺失sectors数据的情况"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = ObsidianReportAgent(obsidian_path=tmpdir)

            test_data = {
                "trade_date": "20240418",
                "top_stocks": [
                    {"code": "000001.SZ", "name": "测试股票", "comprehensive_score": 85.0}
                ]
            }

            result = agent.process(test_data)

            assert result["success"] is True
            # 报告应包含空板块部分
            content = open(result["report_path"], "r", encoding="utf-8").read()
            assert "热门板块" in content

    def test_process_handles_missing_supply_chains(self):
        """测试process()处理缺失supply_chains数据的情况"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = ObsidianReportAgent(obsidian_path=tmpdir)

            test_data = {
                "trade_date": "20240418",
                "top_stocks": [
                    {"code": "000001.SZ", "name": "测试股票", "comprehensive_score": 85.0}
                ]
            }

            result = agent.process(test_data)

            assert result["success"] is True
            # 报告应包含空的产业链分析部分
            content = open(result["report_path"], "r", encoding="utf-8").read()
            assert "产业链分析" in content

    def test_process_handles_missing_industry_distribution(self):
        """测试process()处理缺失industry_distribution数据的情况"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = ObsidianReportAgent(obsidian_path=tmpdir)

            test_data = {
                "trade_date": "20240418",
                "top_stocks": [
                    {"code": "000001.SZ", "name": "测试股票", "comprehensive_score": 85.0}
                ]
            }

            result = agent.process(test_data)

            assert result["success"] is True
            # 报告应包含产业链位置分布部分
            content = open(result["report_path"], "r", encoding="utf-8").read()
            assert "产业链位置分布" in content

    def test_process_handles_missing_data_sources(self):
        """测试process()处理缺失data_sources数据的情况"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = ObsidianReportAgent(obsidian_path=tmpdir)

            test_data = {
                "trade_date": "20240418",
                "top_stocks": [
                    {"code": "000001.SZ", "name": "测试股票", "comprehensive_score": 85.0}
                ]
            }

            result = agent.process(test_data)

            assert result["success"] is True
            # 报告应包含数据来源部分
            content = open(result["report_path"], "r", encoding="utf-8").read()
            assert "数据来源" in content


class TestObsidianReportAgentReportFormat:
    """Tests for ObsidianReportAgent Markdown report format."""

    def test_report_contains_title(self):
        """测试报告包含正确标题"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = ObsidianReportAgent(obsidian_path=tmpdir)

            test_data = {
                "trade_date": "20240418",
                "top_stocks": [],
                "sectors": [],
                "supply_chains": [],
                "industry_distribution": {"upstream": {}, "midstream": {}, "downstream": {}},
                "data_sources": {}
            }

            result = agent.process(test_data)
            content = open(result["report_path"], "r", encoding="utf-8").read()

            assert "# 选股报告" in content
            assert "2024-04-18" in content

    def test_report_contains_generation_time(self):
        """测试报告包含生成时间"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = ObsidianReportAgent(obsidian_path=tmpdir)

            test_data = {
                "trade_date": "20240418",
                "top_stocks": [],
                "sectors": [],
                "supply_chains": [],
                "industry_distribution": {"upstream": {}, "midstream": {}, "downstream": {}},
                "data_sources": {}
            }

            result = agent.process(test_data)
            content = open(result["report_path"], "r", encoding="utf-8").read()

            assert "生成时间" in content

    def test_report_contains_sector_table(self):
        """测试报告包含热门板块表格"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = ObsidianReportAgent(obsidian_path=tmpdir)

            test_data = {
                "trade_date": "20240418",
                "top_stocks": [],
                "sectors": [
                    {
                        "rank": 1,
                        "name": "银行板块",
                        "fund_heat": 85.0,
                        "internet_heat": 75.0,
                        "total_score": 81.0,
                        "logic": "低估值"
                    }
                ],
                "supply_chains": [],
                "industry_distribution": {"upstream": {}, "midstream": {}, "downstream": {}},
                "data_sources": {}
            }

            result = agent.process(test_data)
            content = open(result["report_path"], "r", encoding="utf-8").read()

            assert "热门板块" in content
            assert "银行板块" in content
            assert "资金热度" in content
            assert "互联网热度" in content

    def test_report_contains_stock_table(self):
        """测试报告包含强势股池表格"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = ObsidianReportAgent(obsidian_path=tmpdir)

            test_data = {
                "trade_date": "20240418",
                "top_stocks": [
                    {
                        "rank": 1,
                        "code": "000001.SZ",
                        "name": "平安银行",
                        "comprehensive_score": 85.5,
                        "tech_signal": "突破",
                        "money_signal": "净流入",
                        "core_logic": "估值修复"
                    }
                ],
                "sectors": [],
                "supply_chains": [],
                "industry_distribution": {"upstream": {}, "midstream": {}, "downstream": {}},
                "data_sources": {}
            }

            result = agent.process(test_data)
            content = open(result["report_path"], "r", encoding="utf-8").read()

            assert "强势股池" in content
            assert "平安银行" in content
            assert "000001.SZ" in content
            assert "85.5" in content

    def test_report_contains_supply_chain_analysis(self):
        """测试报告包含产业链分析"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = ObsidianReportAgent(obsidian_path=tmpdir)

            test_data = {
                "trade_date": "20240418",
                "top_stocks": [],
                "sectors": [],
                "supply_chains": [
                    {
                        "sector_name": "银行板块",
                        "upstream": {"name": "招商银行", "code": "600036.SH", "position": "关键资源"},
                        "midstream": {"name": "平安银行", "code": "000001.SZ", "position": "核心制造"},
                        "downstream": {"name": "万科A", "code": "000002.SZ", "position": "终端应用"}
                    }
                ],
                "industry_distribution": {"upstream": {}, "midstream": {}, "downstream": {}},
                "data_sources": {}
            }

            result = agent.process(test_data)
            content = open(result["report_path"], "r", encoding="utf-8").read()

            assert "产业链分析" in content
            assert "银行板块" in content
            assert "招商银行" in content
            assert "600036.SH" in content

    def test_report_contains_industry_distribution(self):
        """测试报告包含产业链位置分布"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = ObsidianReportAgent(obsidian_path=tmpdir)

            test_data = {
                "trade_date": "20240418",
                "top_stocks": [],
                "sectors": [],
                "supply_chains": [],
                "industry_distribution": {
                    "upstream": {"count": 2, "stocks": ["招商银行", "浦发银行"]},
                    "midstream": {"count": 3, "stocks": ["平安银行", "宁波银行"]},
                    "downstream": {"count": 1, "stocks": ["万科A"]}
                },
                "data_sources": {}
            }

            result = agent.process(test_data)
            content = open(result["report_path"], "r", encoding="utf-8").read()

            assert "产业链位置分布" in content
            assert "上游" in content
            assert "中游" in content
            assert "下游" in content

    def test_report_contains_data_sources_section(self):
        """测试报告包含数据来源部分"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = ObsidianReportAgent(obsidian_path=tmpdir)

            test_data = {
                "trade_date": "20240418",
                "top_stocks": [],
                "sectors": [],
                "supply_chains": [],
                "industry_distribution": {"upstream": {}, "midstream": {}, "downstream": {}},
                "data_sources": {
                    "fund_flow": {"source": "Tushare", "update_time": "2024-04-18 16:00"},
                    "internet_heat": {"source": "雪球", "update_time": "2024-04-18 15:30"},
                    "stock_price": {"source": "Tushare", "update_time": "2024-04-18 16:00"}
                }
            }

            result = agent.process(test_data)
            content = open(result["report_path"], "r", encoding="utf-8").read()

            assert "数据来源" in content
            assert "Tushare" in content
            assert "雪球" in content

    def test_report_contains_disclaimer(self):
        """测试报告包含免责声明"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = ObsidianReportAgent(obsidian_path=tmpdir)

            test_data = {
                "trade_date": "20240418",
                "top_stocks": [],
                "sectors": [],
                "supply_chains": [],
                "industry_distribution": {"upstream": {}, "midstream": {}, "downstream": {}},
                "data_sources": {}
            }

            result = agent.process(test_data)
            content = open(result["report_path"], "r", encoding="utf-8").read()

            assert "本报告由自动化选股系统生成" in content
            assert "仅供参考" in content
            assert "不构成投资建议" in content


class TestObsidianReportAgentEdgeCases:
    """Tests for ObsidianReportAgent edge cases."""

    def test_process_handles_invalid_trade_date(self):
        """测试process()处理无效交易日期"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = ObsidianReportAgent(obsidian_path=tmpdir)

            test_data = {
                "trade_date": "invalid-date",
                "top_stocks": [],
                "sectors": [],
                "supply_chains": [],
                "industry_distribution": {"upstream": {}, "midstream": {}, "downstream": {}},
                "data_sources": {}
            }

            # 不应抛出异常，应使用原值或回退
            result = agent.process(test_data)
            assert result["success"] is True

    def test_process_handles_none_values_in_stocks(self):
        """测试process()处理股票数据中的None值"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = ObsidianReportAgent(obsidian_path=tmpdir)

            test_data = {
                "trade_date": "20240418",
                "top_stocks": [
                    {"code": "000001.SZ", "name": None, "comprehensive_score": None}
                ],
                "sectors": [],
                "supply_chains": [],
                "industry_distribution": {"upstream": {}, "midstream": {}, "downstream": {}},
                "data_sources": {}
            }

            result = agent.process(test_data)
            assert result["success"] is True

    def test_process_handles_special_characters_in_stock_names(self):
        """测试process()处理股票名称中的特殊字符"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = ObsidianReportAgent(obsidian_path=tmpdir)

            test_data = {
                "trade_date": "20240418",
                "top_stocks": [
                    {"code": "000001.SZ", "name": "股票*A|B?C", "comprehensive_score": 85.0}
                ],
                "sectors": [],
                "supply_chains": [],
                "industry_distribution": {"upstream": {}, "midstream": {}, "downstream": {}},
                "data_sources": {}
            }

            result = agent.process(test_data)
            # 应该正常处理，不抛出异常
            assert result["success"] is True


class TestObsidianReportAgentDateFormatting:
    """Tests for ObsidianReportAgent date formatting."""

    def test_trade_date_formatting_yyyymmdd(self):
        """测试交易日期格式YYYYMMDD正确转换为YYYY-MM-DD"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = ObsidianReportAgent(obsidian_path=tmpdir)

            test_data = {
                "trade_date": "20240418",
                "top_stocks": [],
                "sectors": [],
                "supply_chains": [],
                "industry_distribution": {"upstream": {}, "midstream": {}, "downstream": {}},
                "data_sources": {}
            }

            result = agent.process(test_data)

            # 文件名应为 2024-04-18.md
            assert os.path.basename(result["report_path"]) == "2024-04-18.md"

            # 内容中的日期也应为 2024-04-18
            content = open(result["report_path"], "r", encoding="utf-8").read()
            assert "2024-04-18" in content

    def test_trade_date_with_slashes(self):
        """测试交易日期格式YYYY/MM/DD"""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = ObsidianReportAgent(obsidian_path=tmpdir)

            test_data = {
                "trade_date": "2024/04/18",
                "top_stocks": [],
                "sectors": [],
                "supply_chains": [],
                "industry_distribution": {"upstream": {}, "midstream": {}, "downstream": {}},
                "data_sources": {}
            }

            result = agent.process(test_data)
            assert result["success"] is True
