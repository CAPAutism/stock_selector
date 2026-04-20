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

from typing import Any, Dict, List, Optional

from stock_selector.agents.base_agent import BaseAgent
from stock_selector.queue.memory_queue import get_queue
from stock_selector.data_sources.tushare_client import TushareClient
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

    def __init__(self, tushare_token: Optional[str] = None):
        """
        初始化StockScreenerAgent

        Args:
            tushare_token: Tushare API Token，如果为None则从环境变量获取
        """
        # 获取输入输出队列
        input_queue = get_queue("chain_analysis")
        output_queue = get_queue("final_stocks")

        super().__init__(
            name="StockScreener",
            input_queue=input_queue,
            output_queue=output_queue
        )

        # 初始化Tushare客户端
        if tushare_token is None:
            import os
            tushare_token = os.environ.get("TUSHARE_TOKEN", "")

        self.tushare_client = TushareClient(tushare_token) if tushare_token else None

        # 初始化股票评分器
        self.scorer = StockScorer()

    def _get_stock_data_from_tushare(self, stock_code: str, trade_date: str) -> Dict[str, Any]:
        """
        从Tushare获取股票数据

        Args:
            stock_code: 股票代码，如000001.SZ
            trade_date: 交易日期，YYYYMMDD

        Returns:
            股票数据字典
        """
        if self.tushare_client is None:
            # 返回默认数据
            return self._get_default_stock_data(stock_code)

        try:
            # 获取日线数据
            daily_data = self.tushare_client.get_daily_data(
                ts_code=stock_code,
                start_date=trade_date,
                end_date=trade_date
            )

            # 获取资金流向数据
            money_flow = self.tushare_client.get_money_flow(
                ts_code=stock_code,
                trade_date=trade_date
            )

            # 构建股票数据
            stock_data = {
                "code": stock_code,
                "name": stock_code,  # 名称需要从其他接口获取，此处简化
            }

            # 处理日线数据
            if daily_data is not None and not daily_data.empty:
                latest = daily_data.iloc[0] if hasattr(daily_data, 'iloc') else daily_data
                stock_data["price_change"] = float(latest.get("pct_chg", 0))
                stock_data["volume_ratio"] = float(latest.get("vol_ratio", 1))
                stock_data["turnover"] = float(latest.get("turnover_rate", 0))

            # 处理资金流向数据
            if money_flow is not None and not money_flow.empty:
                latest = money_flow.iloc[0] if hasattr(money_flow, 'iloc') else money_flow
                stock_data["fund_flow"] = float(latest.get("net_amount", 0))

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

    def _get_stocks_from_sectors(self, sector_codes: List[str]) -> List[str]:
        """
        从板块获取成分股

        Args:
            sector_codes: 板块代码列表

        Returns:
            股票代码列表
        """
        if self.tushare_client is None:
            return []

        all_stocks = []
        for sector_code in sector_codes:
            try:
                stocks = self.tushare_client.get_stocks_in_sector(sector_code)
                all_stocks.extend(stocks)
            except Exception:
                continue

        # 去重
        return list(set(all_stocks))

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
        sector_codes = data.get("sector_codes", [])
        supply_chain = data.get("supply_chain", [])

        # 如果没有sector_codes，尝试从supply_chain构建
        if not sector_codes and supply_chain:
            sector_codes = [s.get("code") for s in supply_chain if s.get("code")]

        # 获取所有相关股票
        stock_codes = self._get_stocks_from_sectors(sector_codes)

        # 获取每只股票的数据并评分
        stocks_to_score = []
        for stock_code in stock_codes:
            stock_data = self._get_stock_data_from_tushare(stock_code, trade_date)
            stocks_to_score.append(stock_data)

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
