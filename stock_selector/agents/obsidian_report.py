"""
ObsidianReportAgent - Obsidian报告生成Agent

职责:
- 从final_stocks队列消费数据
- 生成格式化Markdown报告
- 写入 选股报告/YYYY-MM-DD.md
"""

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from stock_selector.agents.base_agent import BaseAgent
from stock_selector.queue.memory_queue import get_queue


class ObsidianReportAgent(BaseAgent):
    """
    Obsidian报告生成Agent

    职责:
    - 消费final_stocks队列中的选股结果数据
    - 生成格式化Markdown报告
    - 写入 选股报告/YYYY-MM-DD.md
    """

    def __init__(self, obsidian_path: Optional[str] = None):
        """
        初始化ObsidianReportAgent

        Args:
            obsidian_path: Obsidian vault路径，如果为None则从Settings获取
        """
        # 获取输入队列
        input_queue = get_queue("final_stocks")

        # 此Agent输出到文件，没有output_queue
        super().__init__(
            name="ObsidianReport",
            input_queue=input_queue,
            output_queue=None
        )

        # 设置Obsidian路径
        if obsidian_path is None:
            from stock_selector.config.settings import Settings
            settings = Settings()
            obsidian_path = settings.obsidian_vault_path

        self.obsidian_path = obsidian_path

    def _format_trade_date(self, trade_date: str) -> str:
        """
        将交易日期格式从YYYYMMDD转换为YYYY-MM-DD

        Args:
            trade_date: 交易日期字符串，格式为YYYYMMDD或YYYY/MM/DD

        Returns:
            格式化后的日期字符串 YYYY-MM-DD
        """
        # 移除非数字字符
        date_str = ''.join(c for c in trade_date if c.isdigit())

        if len(date_str) == 8:
            return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
        elif len(date_str) == 6:
            # 可能是YYMMDD格式
            return f"20{date_str[:2]}-{date_str[2:4]}-{date_str[4:6]}"

        # 回退：返回原值
        return trade_date

    def _get_or_create_report_dir(self) -> str:
        """
        获取或创建报告目录

        Returns:
            报告目录路径
        """
        report_dir = os.path.join(self.obsidian_path, "选股报告")
        if not os.path.exists(report_dir):
            os.makedirs(report_dir, exist_ok=True)
        return report_dir

    def _build_sector_table(self, sectors: List[Dict[str, Any]]) -> str:
        """
        构建热门板块表格

        Args:
            sectors: 板块数据列表

        Returns:
            Markdown格式的表格
        """
        if not sectors:
            return "| 排名 | 板块名称 | 资金热度 | 互联网热度 | 综合分 |\n|:---:|:--------|:--------|:---------|:------:|\n| - | 暂无数据 | - | - | - |"

        lines = [
            "| 排名 | 板块名称 | 资金热度 | 互联网热度 | 综合分 |",
            "|:---:|:--------|:--------|:---------|:------:|"
        ]

        for sector in sectors:
            rank = sector.get("rank", "-")
            name = sector.get("name", "-")
            fund_heat = sector.get("fund_flow_score", sector.get("score", 0))
            internet_heat = sector.get("heat_score", 0)
            total_score = sector.get("score", sector.get("total_score", 0))
            lines.append(f"| {rank} | {name} | {fund_heat:.1f} | {internet_heat:.1f} | {total_score:.1f} |")

        return "\n".join(lines)

    def _build_sector_logic_section(self, sectors: List[Dict[str, Any]]) -> str:
        """
        构建板块驱动逻辑部分

        Args:
            sectors: 板块数据列表

        Returns:
            Markdown格式的板块驱动逻辑
        """
        if not sectors:
            return "暂无板块驱动逻辑数据"

        lines = []
        for sector in sectors[:5]:  # 只取前5个板块
            name = sector.get("name", "-")
            logic = sector.get("logic", "暂无分析")
            lines.append(f"- **{name}**: {logic}")

        return "\n".join(lines) if lines else "暂无板块驱动逻辑数据"

    def _build_supply_chain_table(self, supply_chains: List[Dict[str, Any]]) -> str:
        """
        构建产业链分析表格

        Args:
            supply_chains: 产业链数据列表

        Returns:
            Markdown格式的产业链分析
        """
        if not supply_chains:
            return "暂无产业链数据"

        lines = []

        for chain in supply_chains:
            sector_name = chain.get("sector_name", "-")
            lines.append(f"### {sector_name} 产业链\n")
            lines.append("| 环节 | 代表股票 | 代码 | 产业地位 |")
            lines.append("|:----:|:--------|:-----|:--------:|")

            for position_key in ["upstream", "midstream", "downstream"]:
                position_data = chain.get(position_key, [])
                # 处理列表格式的产业链数据
                if isinstance(position_data, list) and position_data:
                    first_stock = position_data[0]
                    name = first_stock.get("name", "-") if isinstance(first_stock, dict) else "-"
                    code = first_stock.get("code", "-") if isinstance(first_stock, dict) else "-"
                    position = position_key.capitalize()
                    lines.append(f"| {position_key.capitalize()} | {name} | {code} | {position} |")
                elif isinstance(position_data, dict):
                    name = position_data.get("name", "-")
                    code = position_data.get("code", "-")
                    position = position_data.get("position", "-")
                    lines.append(f"| {position_key.capitalize()} | {name} | {code} | {position} |")

            lines.append("\n---\n")

        return "\n".join(lines)

    def _build_stock_table(self, top_stocks: List[Dict[str, Any]]) -> str:
        """
        构建强势股池表格

        Args:
            top_stocks: 股票数据列表

        Returns:
            Markdown格式的强势股池表格
        """
        if not top_stocks:
            return "| 排名 | 股票名称 | 代码 | 综合分 | 技术信号 | 资金信号 | 核心逻辑 |\n|:---:|:--------|:-----|:------:|:--------|:--------|:--------|\n| - | 暂无数据 | - | - | - | - | - |"

        lines = [
            "| 排名 | 股票名称 | 代码 | 综合分 | 技术信号 | 资金信号 | 核心逻辑 |",
            "|:---:|:--------|:-----|:------:|:--------|:--------|:--------|"
        ]

        for stock in top_stocks:
            rank = stock.get("rank", "-")
            name = stock.get("name") or "-"
            code = stock.get("code", "-")
            score = stock.get("comprehensive_score")
            if score is not None:
                score_str = f"{score:.1f}"
            else:
                score_str = "-"
            tech_signal = stock.get("tech_signal", "-") or "-"
            money_signal = stock.get("money_signal", "-") or "-"
            core_logic = stock.get("core_logic", "-") or "-"
            lines.append(f"| {rank} | {name} | {code} | {score_str} | {tech_signal} | {money_signal} | {core_logic} |")

        return "\n".join(lines)

    def _build_industry_distribution_table(self, industry_distribution: Dict[str, Any]) -> str:
        """
        构建产业链位置分布表格

        Args:
            industry_distribution: 产业链分布数据

        Returns:
            Markdown格式的产业链位置分布表格
        """
        if not industry_distribution:
            return "| 产业链环节 | 入选数量 | 代表股 |\n|:---------:|:--------:|:------|\n| 上游 | 0 | 暂无数据 |\n| 中游 | 0 | 暂无数据 |\n| 下游 | 0 | 暂无数据 |"

        lines = [
            "| 产业链环节 | 入选数量 | 代表股 |",
            "|:---------:|:--------:|:------|"
        ]

        position_mapping = {
            "upstream": "上游",
            "midstream": "中游",
            "downstream": "下游"
        }

        for position in ["upstream", "midstream", "downstream"]:
            data = industry_distribution.get(position, {})
            count = data.get("count", 0)
            stocks = data.get("stocks", [])
            stock_list = ", ".join(stocks) if stocks else "暂无数据"
            position_name = position_mapping.get(position, position)
            lines.append(f"| {position_name} | {count} | {stock_list} |")

        return "\n".join(lines)

    def _build_data_sources_section(self, data_sources: Dict[str, Any]) -> str:
        """
        构建数据来源部分

        Args:
            data_sources: 数据来源配置

        Returns:
            Markdown格式的数据来源表格
        """
        if not data_sources:
            return "| 数据类型 | 来源 | 更新时间 |\n|:---------|:-----|:---------|\n| 板块资金流向 | 暂无数据 | - |\n| 互联网热度 | 暂无数据 | - |\n| 个股行情 | 暂无数据 | - |"

        lines = [
            "| 数据类型 | 来源 | 更新时间 |",
            "|:---------|:-----|:---------|"
        ]

        source_mapping = {
            "fund_flow": "板块资金流向",
            "internet_heat": "互联网热度",
            "stock_price": "个股行情"
        }

        for key, display_name in source_mapping.items():
            if key in data_sources:
                source_data = data_sources[key]
                source = source_data.get("source", "-")
                update_time = source_data.get("update_time", "-")
            else:
                source = "-"
                update_time = "-"
            lines.append(f"| {display_name} | {source} | {update_time} |")

        return "\n".join(lines)

    def _generate_markdown_report(self, data: Dict[str, Any]) -> str:
        """
        生成Markdown格式的报告

        Args:
            data: 选股结果数据

        Returns:
            Markdown格式的报告内容
        """
        trade_date = data.get("trade_date", "")
        formatted_date = self._format_trade_date(trade_date)
        generation_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 提取数据 - 从多个可能的来源获取板块数据
        top_stocks = data.get("top_stocks", [])
        sectors = data.get("sectors", data.get("top_sectors", []))
        supply_chains = data.get("supply_chains", data.get("chain_structures", []))
        industry_distribution = data.get("industry_distribution", {})
        data_sources = data.get("data_sources", {})

        # 构建报告各部分
        sector_table = self._build_sector_table(sectors)
        sector_logic = self._build_sector_logic_section(sectors)
        supply_chain_content = self._build_supply_chain_table(supply_chains)
        stock_table = self._build_stock_table(top_stocks)
        industry_dist_table = self._build_industry_distribution_table(industry_distribution)
        data_sources_content = self._build_data_sources_section(data_sources)

        # 组装完整报告
        report = f"""# 选股报告 - {formatted_date}

> 生成时间: {generation_time}

## 热门板块

{sector_table}

### 板块驱动逻辑
{sector_logic}

---

## 产业链分析

{supply_chain_content}

## 强势股池

### 综合评分Top10

{stock_table}

### 产业链位置分布

{industry_dist_table}

---

## 数据来源

{data_sources_content}

---

> 本报告由自动化选股系统生成，仅供参考，不构成投资建议。
"""

        return report

    def process(self, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        处理选股结果数据，生成Markdown报告

        Args:
            data: 可选的输入数据。如果为None，从input_queue获取数据。

        Returns:
            处理结果字典，包含success和report_path
        """
        # 如果没有传入数据，从输入队列获取
        if data is None:
            data = self.receive().data

        # 提取交易日期
        trade_date = data.get("trade_date", "")
        formatted_date = self._format_trade_date(trade_date)

        # 获取或创建报告目录
        report_dir = self._get_or_create_report_dir()

        # 生成报告文件路径
        report_filename = f"{formatted_date}.md"
        report_path = os.path.join(report_dir, report_filename)

        # 生成Markdown报告
        report_content = self._generate_markdown_report(data)

        # 写入文件
        try:
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report_content)
            success = True
        except Exception as e:
            success = False
            report_path = None

        # 返回结果
        return {
            "success": success,
            "report_path": report_path,
            "trade_date": formatted_date
        }
