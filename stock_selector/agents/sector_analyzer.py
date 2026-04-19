"""
SectorAnalyzerAgent - 板块热度分析Agent

职责:
- 从raw_market_data队列消费数据
- 结合资金流向数据(权重60%)和热度数据(权重40%)计算板块综合分数
- 输出Top5热门板块到sector_analysis队列

公式: 板块热度分 = 0.6 × 资金分 + 0.4 × 热度分
"""

from typing import Any, Dict, List, Optional

from stock_selector.agents.base_agent import BaseAgent
from stock_selector.queue.memory_queue import get_queue
from scorers.sector_scorer import (
    SectorScorer,
    calculate_fund_flow_score,
    calculate_heat_score,
    calculate_sector_score,
)


class SectorAnalyzerAgent(BaseAgent):
    """
    板块热度分析Agent

    职责:
    - 消费raw_market_data队列中的数据
    - 计算板块综合热度分数
    - 输出Top5热门板块到sector_analysis队列
    """

    def __init__(self):
        """
        初始化SectorAnalyzerAgent
        """
        # 获取输入输出队列
        input_queue = get_queue("raw_market_data")
        output_queue = get_queue("sector_analysis")

        super().__init__(
            name="SectorAnalyzer",
            input_queue=input_queue,
            output_queue=output_queue
        )

        # 初始化板块评分器
        self.scorer = SectorScorer()

    def process(self, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        处理板块数据，计算综合热度分数

        Args:
            data: 可选的输入数据。如果为None，从input_queue获取数据。

        Returns:
            处理结果字典，包含top_sectors和trade_date
        """
        # 如果没有传入数据，从输入队列获取
        if data is None:
            data = self.receive().data

        # 提取数据
        trade_date = data.get("trade_date", "")
        sectors_fund_flow = data.get("sectors_fund_flow", [])
        sectors_heat = data.get("sectors_heat", [])

        # 构建热度字典便于查找
        heat_dict = {
            h.get("code"): h.get("heat_value", 0)
            for h in sectors_heat
        }

        # 构建板块列表，计算综合分数
        sectors_to_score = []
        for fund_flow in sectors_fund_flow:
            code = fund_flow.get("code", "")
            name = fund_flow.get("name", "")
            rank = fund_flow.get("rank", 0)

            # 获取热度值
            heat_value = heat_dict.get(code, 0)

            sectors_to_score.append({
                "code": code,
                "name": name,
                "fund_flow_rank": rank,
                "heat_value": heat_value
            })

        # 使用评分器计算分数并排序
        scored_sectors = self.scorer.score_sectors(sectors_to_score)

        # 取Top5
        top_5 = scored_sectors[:5]

        # 构建结果
        result = {
            "trade_date": trade_date,
            "top_sectors": top_5,
            "total_sectors_analyzed": len(scored_sectors)
        }

        # 发送结果到输出队列
        self.send(result)

        return result
