"""
ChainAnalyzerAgent - 产业链分析Agent

职责:
- 从sector_analysis队列消费数据(Top5热门板块)
- 获取板块内个股的产业链位置信息
- 分析个股在上游/中游/下游的分布
- 输出产业链结构到chain_analysis队列
"""

from typing import Any, Dict, List, Optional

from stock_selector.agents.base_agent import BaseAgent
from stock_selector.queue.memory_queue import get_queue
from stock_selector.data_sources.tushare_client import TushareClient
from scorers.chain_scorer import ChainScorer


class ChainAnalyzerAgent(BaseAgent):
    """
    产业链分析Agent

    职责:
    - 消费sector_analysis队列中的Top5热门板块
    - 获取板块成分股并分析其产业链位置
    - 输出产业链结构(上游/中游/下游)到chain_analysis队列
    """

    def __init__(self):
        """
        初始化ChainAnalyzerAgent
        """
        # 获取输入输出队列
        input_queue = get_queue("sector_analysis")
        output_queue = get_queue("chain_analysis")

        super().__init__(
            name="ChainAnalyzer",
            input_queue=input_queue,
            output_queue=output_queue
        )

        # 初始化产业链评分器
        self.chain_scorer = ChainScorer()

        # 初始化Tushare客户端(使用环境变量中的token)
        import os
        token = os.environ.get("TUSHARE_TOKEN", "")
        self.tushare_client = TushareClient(token) if token else None

    def _classify_stock_position(self, stock_code: str, sector_code: str) -> str:
        """
        根据股票代码和板块信息分类产业链位置

        这里使用简单的启发式方法:
        - 股票代码尾数模3取余
        - 0->上游, 1->中游, 2->下游

        实际生产中应该使用更复杂的产业链数据

        Args:
            stock_code: 股票代码
            sector_code: 板块代码

        Returns:
            产业链位置: 'upstream', 'midstream', 或 'downstream'
        """
        # 简单的哈希分类方法
        # 实际应该接入产业链数据库
        if not stock_code:
            return "midstream"

        # 使用股票代码的数值特征进行分类
        try:
            code_num = int(stock_code.replace(".", "").replace(",", ""))
            position = code_num % 3
            if position == 0:
                return "upstream"
            elif position == 1:
                return "midstream"
            else:
                return "downstream"
        except ValueError:
            return "midstream"

    def _get_stocks_in_sectors(self, sectors: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        获取各板块的成分股

        Args:
            sectors: 板块列表

        Returns:
            Dict: {sector_code: [stock_codes]}
        """
        if not self.tushare_client:
            # 如果没有Tushare客户端，使用模拟数据
            return {
                sector.get("code", ""): [f"stock{i:03d}" for i in range(3)]
                for sector in sectors
            }

        stocks_by_sector = {}
        for sector in sectors:
            sector_code = sector.get("code", "")
            if sector_code:
                stocks = self.tushare_client.get_stocks_in_sector(sector_code)
                stocks_by_sector[sector_code] = stocks if stocks else []

        return stocks_by_sector

    def _build_chain_structure(
        self,
        sector: Dict[str, Any],
        stocks: List[str]
    ) -> Dict[str, Any]:
        """
        构建单个板块的产业链结构

        Args:
            sector: 板块信息
            stocks: 成分股列表

        Returns:
            包含上中下游结构的字典
        """
        sector_code = sector.get("code", "")
        sector_name = sector.get("name", "")

        # 初始化上中下游
        chain_data = {
            "upstream": [],
            "midstream": [],
            "downstream": []
        }

        # 对每只股票进行分类
        for stock_code in stocks:
            link_type = self._classify_stock_position(stock_code, sector_code)
            stock_info = {
                "code": stock_code,
                "name": f"{sector_name}_{stock_code}",  # 简化名称
                "sector_code": sector_code,
                "sector_name": sector_name
            }
            chain_data[link_type].append(stock_info)

        # 使用ChainScorer进行评分
        scored_stocks = self.chain_scorer.score_chain_positions(chain_data)

        # 重新组织为上中下游结构
        result = {
            "sector_code": sector_code,
            "sector_name": sector_name,
            "sector_score": sector.get("score", 0),
            "upstream": [],
            "midstream": [],
            "downstream": []
        }

        for stock in scored_stocks:
            link_type = stock.get("link_type", "midstream")
            result[link_type].append(stock)

        return result

    def process(self, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        处理板块数据，分析产业链结构

        Args:
            data: 可选的输入数据。如果为None，从input_queue获取数据。

        Returns:
            处理结果字典，包含chain_structures和统计信息
        """
        # 如果没有传入数据，从输入队列获取
        if data is None:
            data = self.receive().data

        # 提取数据
        trade_date = data.get("trade_date", "")
        top_sectors = data.get("top_sectors", [])
        total_sectors_analyzed = data.get("total_sectors_analyzed", 0)

        # 获取各板块的成分股
        stocks_by_sector = self._get_stocks_in_sectors(top_sectors)

        # 构建产业链结构
        chain_structures = []
        total_stocks = 0

        for sector in top_sectors:
            sector_code = sector.get("code", "")
            stocks = stocks_by_sector.get(sector_code, [])

            chain_structure = self._build_chain_structure(sector, stocks)
            chain_structures.append(chain_structure)

            total_stocks += len(stocks)

        # 构建结果
        result = {
            "trade_date": trade_date,
            "chain_structures": chain_structures,
            "total_sectors_analyzed": len(top_sectors),
            "total_stocks_analyzed": total_stocks
        }

        # 发送结果到输出队列
        self.send(result)

        return result
