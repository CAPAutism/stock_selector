"""
数据采集Agent

负责从AKShare获取板块资金流向数据，从互联网获取热度数据
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from stock_selector.agents.base_agent import BaseAgent
from stock_selector.data_sources.akshare_client import AKShareClient
from stock_selector.queue.memory_queue import get_queue
from stock_selector.config.settings import Settings


class DataCollectorAgent(BaseAgent):
    """
    数据采集Agent

    职责:
    - 从AKShare获取板块资金流向（免费数据）
    - 从互联网获取热度数据(预留接口)
    - 将聚合数据写入raw_market_data队列
    """

    def __init__(self, token: Optional[str] = None):
        """
        初始化数据采集Agent

        Args:
            token: Tushare API Token（可选，用于备选）
        """
        settings = Settings()
        self.token = token or settings.tushare_token
        self.akshare_client = AKShareClient()
        self.settings = settings

        # 获取输出队列
        output_queue = get_queue("raw_market_data")

        super().__init__(
            name="DataCollector",
            input_queue=None,
            output_queue=output_queue
        )

    def process(self, data: Any = None) -> Dict[str, Any]:
        """
        处理数据: 采集板块资金流向和热度数据

        Args:
            data: 可选的输入数据(此Agent不需要输入)

        Returns:
            采集的数据字典
        """
        result = self.collect()

        # 自动发送到输出队列
        self.send(result)

        return result

    def collect(self) -> Dict[str, Any]:
        """
        执行数据采集

        Returns:
            采集的数据，包含:
            - trade_date: 交易日期
            - sectors_fund_flow: 板块资金流向列表
            - sectors_heat: 板块热度数据(预留接口)
            - timestamp: 采集时间
        """
        trade_date = datetime.now().strftime("%Y%m%d")

        # 采集板块资金流向 (使用AKShare免费接口)
        sectors_fund_flow = self._collect_sector_fund_flow(trade_date)

        # 采集热度数据(预留接口)
        sectors_heat = self._collect_heat_data(trade_date)

        result = {
            "trade_date": trade_date,
            "sectors_fund_flow": sectors_fund_flow,
            "sectors_heat": sectors_heat,
            "timestamp": datetime.now().timestamp()
        }

        return result

    def _collect_sector_fund_flow(self, trade_date: str) -> List[Dict[str, Any]]:
        """
        采集板块资金流向数据

        Args:
            trade_date: 交易日期

        Returns:
            板块资金流向列表
        """
        try:
            df = self.akshare_client.get_sector_fund_flow(indicator="今日")
            if df is None or df.empty:
                return []

            # 转换为字典列表
            records = []
            for _, row in df.iterrows():
                records.append({
                    "code": str(row.get("code", "")),
                    "name": str(row.get("name", "")),
                    "close": row.get("close", 0),
                    "change": row.get("change", 0),
                    "amount": row.get("amount", 0),
                    "main_amount": row.get("main_amount", 0),
                    "rank": row.get("rank", 0)
                })

            return records
        except Exception as e:
            print(f"采集板块资金流向失败: {e}")
            return []

    def _collect_heat_data(self, trade_date: str) -> List[Dict[str, Any]]:
        """
        采集互联网热度数据

        TODO: 实现真实的互联网热度数据获取
        - 雪球热度API
        - 微博搜索指数
        - 微信公众号热度

        Args:
            trade_date: 交易日期

        Returns:
            板块热度数据列表(目前返回空列表，待HeatClient实现)
        """
        # 预留接口，目前返回空数据
        # 后续可接入:
        # - 雪球热度API
        # - 微博搜索指数
        # - 微信公众号热度
        return []

    def run_once(self) -> Dict[str, Any]:
        """
        执行一次数据采集并返回结果

        用于定时任务调用

        Returns:
            采集的数据字典
        """
        return self.collect()
