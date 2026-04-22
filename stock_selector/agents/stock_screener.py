"""
StockScreenerAgent - 选股Agent

职责:
- 从chain_analysis队列消费数据
- 获取供应链相关股票数据
- 计算综合分数: 技术40% + 基本面30% + 资金30%
- 输出Top10强势股票到final_stocks队列

公式: 综合分 = 0.4 × 技术分 + 0.3 × 基本面分 + 0.3 × 资金分
技术分 = 涨跌幅得分(25%) + 放量得分(25%) + 趋势得分(50%)
基本面分 = 业绩增速(40%) + 估值合理度(30%) + 成长性(30%)
资金分 = 主力净流入(50%) + 筹码集中度(50%)
"""

import random
from typing import Any, Dict, List, Optional

from stock_selector.agents.base_agent import BaseAgent
from stock_selector.queue.memory_queue import get_queue
from stock_selector.data_sources.akshare_client import AKShareClient
from scorers.stock_scorer import StockScorer


class StockScreenerAgent(BaseAgent):
    """
    选股Agent

    职责:
    - 消费chain_analysis队列中的数据
    - 获取供应链相关板块的成分股
    - 计算股票综合分数
    - 输出Top10强势股票到final_stocks队列
    """

    def __init__(self):
        """
        初始化StockScreenerAgent
        """
        # 获取输入输出队列
        input_queue = get_queue("chain_analysis")
        output_queue = get_queue("final_stocks")

        super().__init__(
            name="StockScreener",
            input_queue=input_queue,
            output_queue=output_queue
        )

        # 初始化AKShare客户端
        self.akshare_client = AKShareClient()

        # 初始化股票评分器
        self.scorer = StockScorer()

    def _get_stock_data_from_akshare(self, stock_code: str, trade_date: str) -> Dict[str, Any]:
        """
        从AKShare获取股票数据

        Args:
            stock_code: 股票代码，如000001
            trade_date: 交易日期，YYYYMMDD

        Returns:
            股票数据字典
        """
        try:
            # 转换代码格式
            ts_code = stock_code
            if '.' not in ts_code:
                suffix = '.SZ' if ts_code.startswith(('000', '001', '002', '300')) else '.SH'
                ts_code = ts_code + suffix

            # 获取日线数据
            df = self.akshare_client.get_stock_daily(ts_code, trade_date, trade_date)

            # 构建股票数据
            stock_data = {
                "code": stock_code,
                "name": stock_code,
            }

            # 处理日线数据
            if df is not None and not df.empty:
                latest = df.iloc[0] if hasattr(df, 'iloc') else df
                stock_data["price_change"] = float(latest.get("涨跌幅", 0))
                stock_data["volume_ratio"] = float(latest.get("成交量", 1)) / 1000000
                stock_data["turnover"] = float(latest.get("换手率", 0))
                stock_data["fund_flow"] = float(latest.get("成交额", 0))

            return stock_data

        except Exception as e:
            # 发生错误时返回默认数据
            return self._get_default_stock_data(stock_code)

    def _get_default_stock_data(self, stock_code: str) -> Dict[str, Any]:
        """
        获取默认股票数据（当无法获取真实数据时使用）

        Args:
            stock_code: 股票代码

        Returns:
            默认股票数据字典
        """
        return {
            "code": stock_code,
            "name": stock_code,
            "price_change": 0,
            "volume_ratio": 1,
            "trend": "neutral",
            "earnings_growth": 0,
            "valuation": 20,
            "growth": 0,
            "fund_flow": 0,
            "chip_concentration": 0.5
        }

    def _get_stocks_from_chain(self, chain_structures: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        从产业链结构中提取股票

        Args:
            chain_structures: 产业链结构列表

        Returns:
            股票列表（含位置信息）
        """
        all_stocks = []

        for chain in chain_structures:
            sector_name = chain.get("sector_name", "")

            for link_type in ["upstream", "midstream", "downstream"]:
                stocks = chain.get(link_type, [])
                for stock in stocks:
                    stock_copy = stock.copy()
                    stock_copy["link_type"] = link_type
                    stock_copy["sector_name"] = sector_name
                    all_stocks.append(stock_copy)

        # 如果没有股票，使用模拟数据
        if not all_stocks:
            for i in range(10):
                all_stocks.append({
                    "code": f"stock{i:03d}",
                    "name": f"模拟股票{i:03d}",
                    "link_type": ["upstream", "midstream", "downstream"][i % 3],
                    "price_change": random.uniform(-5, 5),
                    "volume_ratio": random.uniform(0.5, 2),
                    "fund_flow": random.uniform(-1000, 1000),
                })

        return all_stocks

    def process(self, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        处理板块数据，计算股票综合分数

        Args:
            data: 可选的输入数据。如果为None，从input_queue获取数据。

        Returns:
            处理结果字典，包含top_stocks和trade_date
        """
        # 如果没有传入数据，从输入队列获取
        if data is None:
            data = self.receive().data

        # 提取数据
        trade_date = data.get("trade_date", "")
        chain_structures = data.get("chain_structures", [])

        # 从产业链结构获取股票
        stocks_to_score = self._get_stocks_from_chain(chain_structures)

        # 获取每只股票的数据并评分
        for stock in stocks_to_score:
            # 获取实时数据（如果可能）
            stock_code = stock.get("code", "")
            stock_data = self._get_stock_data_from_akshare(stock_code, trade_date)
            # 合并数据
            stock.update(stock_data)

        # 使用评分器计算分数并排序
        scored_stocks = self.scorer.score_stocks(stocks_to_score, top_n=10)

        # 取Top10
        top_10 = scored_stocks[:10]

        # 构建结果
        result = {
            "trade_date": trade_date,
            "top_stocks": top_10,
            "total_stocks_analyzed": len(scored_stocks)
        }

        # 发送结果到输出队列
        self.send(result)

        return result
