"""
Tushare数据源客户端

封装Tushare Pro API，提供A股数据获取接口
"""

import tushare as ts
import pandas as pd
from typing import Optional, List, Dict, Any
from datetime import date, datetime

class TushareClient:
    """
    Tushare Pro API客户端

    提供A股市场数据获取接口
    """

    def __init__(self, token: str):
        """
        初始化Tushare客户端

        Args:
            token: Tushare Pro API Token
        """
        self.token = token
        ts.set_token(token)
        self.pro = ts.pro_api()

    def get_sector_fund_flow(self, trade_date: Optional[str] = None) -> pd.DataFrame:
        """
        获取概念板块资金流向

        Args:
            trade_date: 交易日期，格式YYYYMMDD，默认今日

        Returns:
            板块资金流向数据，包含:
            - code: 板块代码
            - name: 板块名称
            - close: 收盘点位
            - change: 涨跌幅
            - amount: 成交额(万元)
            - main_amount: 主力净流入额(万元)
        """
        if trade_date is None:
            trade_date = datetime.now().strftime("%Y%m%d")

        try:
            df = self.pro.ths_dp(trade_date=trade_date)
            return df
        except Exception as e:
            print(f"获取板块资金流向失败: {e}")
            return pd.DataFrame()

    def get_daily_data(self, ts_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        获取个股日线数据

        Args:
            ts_code: 股票代码，如000001.SZ
            start_date: 开始日期，YYYYMMDD
            end_date: 结束日期，YYYYMMDD

        Returns:
            日线数据
        """
        try:
            df = self.pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
            return df
        except Exception as e:
            print(f"获取日线数据失败: {e}")
            return pd.DataFrame()

    def get_money_flow(self, ts_code: str, trade_date: str) -> pd.DataFrame:
        """
        获取个股资金流向

        Args:
            ts_code: 股票代码
            trade_date: 交易日期，YYYYMMDD

        Returns:
            资金流向数据
        """
        try:
            df = self.pro.moneyflow(ts_code=ts_code, trade_date=trade_date)
            return df
        except Exception as e:
            print(f"获取资金流向失败: {e}")
            return pd.DataFrame()

    def get_stocks_in_sector(self, sector_code: str) -> List[str]:
        """
        获取板块成分股

        Args:
            sector_code: 板块代码

        Returns:
            成分股代码列表
        """
        try:
            df = self.pro.ths_member(ts_code=sector_code)
            if df is not None and not df.empty:
                return df['code'].tolist()
            return []
        except Exception as e:
            print(f"获取板块成分股失败: {e}")
            return []