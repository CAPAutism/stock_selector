import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class Settings:
    """系统配置管理"""

    # Tushare配置
    tushare_token: str = "bcd5ead04df2b3ccd18af6f48278c1ad038154616c47835d608c68b4"

    # Obsidian配置
    obsidian_vault_path: str = os.path.expanduser("~/Documents/vault")

    # 选股配置
    top_sectors_count: int = 5          # 热门板块数量
    top_stocks_count: int = 10          # 入选股票数量

    # 评分权重
    fund_flow_weight: float = 0.6       # 资金流向权重(板块)
    heat_weight: float = 0.4            # 热度权重(板块)

    tech_weight: float = 0.4            # 技术面权重(个股)
    fundamental_weight: float = 0.3     # 基本面权重(个股)
    money_weight: float = 0.3          # 资金面权重(个股)

    # 产业链配置
    upstream_weight: float = 1.2        # 上游权重
    midstream_weight: float = 1.0       # 中游权重
    downstream_weight: float = 0.8       # 下游权重

    @property
    def obsidian_report_dir(self) -> str:
        """Obsidian报告目录路径"""
        return os.path.join(self.obsidian_vault_path, "选股报告")
