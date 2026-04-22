"""
AKShare数据源客户端

基于AKShare的免费A股数据接口，提供板块资金流向和热度数据
"""

import akshare as ak
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import time

logger = logging.getLogger(__name__)


class AKShareClient:
    """
    AKShare API客户端 - 免费数据源

    提供A股市场数据获取接口，无需API Key
    """

    def __init__(self, retry_count: int = 3, retry_delay: float = 1.0):
        """初始化AKShare客户端"""
        self.retry_count = retry_count
        self.retry_delay = retry_delay

    def _retry_call(self, func, *args, **kwargs):
        """带重试的API调用"""
        last_error = None
        for i in range(self.retry_count):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                if i < self.retry_count - 1:
                    time.sleep(self.retry_delay)
        logger.error(f"API调用失败，已重试{self.retry_count}次: {last_error}")
        return None

    def get_sector_fund_flow(self, indicator: str = "今日") -> pd.DataFrame:
        """
        获取板块资金流向排名

        Args:
            indicator: 时间周期，"今日"、"5日"、"10日"

        Returns:
            板块资金流向数据，包含:
            - code: 板块代码
            - name: 板块名称
            - change: 涨跌幅
            - main_amount: 主力净流入额
            - rank: 排名
        """
        try:
            # 使用stock_sector_spot获取板块数据
            df = self._retry_call(ak.stock_sector_spot)
            if df is None or df.empty:
                return pd.DataFrame()

            # 解析列名（stock_sector_spot返回的列名是中文但显示为乱码）
            # 根据位置映射列
            # 0: label (板块代码), 1: 板块名称, 2: 公司数量, 3: 平均价格
            # 4: 涨跌幅, 5: 涨跌额, 6: 成交额, 7: 成交量
            # 8: 领涨股票代码, 9-11: 主力净流入相关, 12: 领涨股票名称
            result = pd.DataFrame()
            result['code'] = df.iloc[:, 0]  # label列
            result['name'] = df.iloc[:, 1]  # 板块名称列
            result['change'] = pd.to_numeric(df.iloc[:, 4], errors='coerce').fillna(0)  # 涨跌幅列
            # 主力净流入使用"主力净流入-净额"列（通常是第10列或类似）
            main_col_idx = None
            for idx, col in enumerate(df.columns):
                if '主力' in str(col) and '净额' in str(col):
                    main_col_idx = idx
                    break
            if main_col_idx is None:
                main_col_idx = 10  # 默认第10列
            result['main_amount'] = pd.to_numeric(df.iloc[:, main_col_idx], errors='coerce').fillna(0)

            # 计算排名（按主力净流入降序）
            result = result.sort_values('main_amount', ascending=False).reset_index(drop=True)
            result['rank'] = range(1, len(result) + 1)

            return result
        except Exception as e:
            logger.error(f"获取板块资金流向失败: {e}")
            return pd.DataFrame()

    def get_hot_sectors(self, date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取热门板块/概念

        Args:
            date: 日期，格式YYYYMMDD，默认今日

        Returns:
            热门板块列表
        """
        try:
            # 东方财富热门板块数据
            df = self._retry_call(ak.stock_hot_rank_em)
            if df is None or df.empty:
                return []

            # 提取前20名热门板块
            results = []
            for i, row in df.head(20).iterrows():
                results.append({
                    "code": str(row.get('代码', '')),
                    "name": str(row.get('名称', '')),
                    "rank": i + 1
                })
            return results
        except Exception as e:
            logger.error(f"获取热门板块失败: {e}")
            return []

    def get_stock_daily(self, ts_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        获取个股日线数据

        Args:
            ts_code: 股票代码，如000001
            start_date: 开始日期 YYYYMMDD
            end_date: 结束日期 YYYYMMDD

        Returns:
            日线数据
        """
        try:
            # 转换代码格式
            if '.' not in ts_code:
                suffix = '.SZ' if ts_code.startswith(('000', '001', '002', '300')) else '.SH'
                ts_code = ts_code + suffix

            df = self._retry_call(ak.stock_zh_a_hist, symbol=ts_code, start_date=start_date, end_date=end_date)
            if df is None or df.empty:
                return pd.DataFrame()

            return df
        except Exception as e:
            logger.error(f"获取个股日线数据失败: {e}")
            return pd.DataFrame()

    def get_sector_stocks(self, sector_name: str) -> List[str]:
        """
        获取板块成分股

        Args:
            sector_name: 板块名称

        Returns:
            成分股代码列表
        """
        try:
            df = self._retry_call(ak.stock_sector_spot)
            if df is None or df.empty:
                return []

            # 查找对应板块
            sector_df = df[df.iloc[:, 1] == sector_name]
            if sector_df.empty:
                return []

            # 获取成分股
            codes = sector_df.iloc[0, 8] if len(df.columns) > 8 else ''  # 领涨股票代码列
            if isinstance(codes, str):
                return codes.split(',')
            return [codes] if codes else []
        except Exception as e:
            logger.error(f"获取板块成分股失败: {e}")
            return []

    def get_concept_sector_fund_flow(self) -> pd.DataFrame:
        """
        获取概念板块资金流向

        Returns:
            概念板块资金流向数据
        """
        try:
            df = self._retry_call(ak.stock_sector_fund_flow_summary, symbol="人工智能", indicator="今日")
            if df is None or df.empty:
                return pd.DataFrame()
            return df
        except Exception as e:
            logger.error(f"获取概念板块资金流向失败: {e}")
            return pd.DataFrame()