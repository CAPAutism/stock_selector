from datetime import date, datetime, timedelta
from typing import Optional

# 中国A股交易日历(简化版，实际应接入数据源)
TRADE_CALENDAR = {
    # 2024年部分交易日
    "2024-04-15", "2024-04-16", "2024-04-17",
    "2024-04-18", "2024-04-19", "2024-04-22",
}

def format_date(d: date) -> str:
    """格式化日期为YYYY-MM-DD字符串"""
    return d.strftime("%Y-%m-%d")

def is_trade_day(d: date) -> bool:
    """判断是否为交易日(简化版)"""
    # 周末直接返回False
    if d.weekday() >= 5:
        return False
    # 检查是否为已知交易日
    date_str = format_date(d)
    return date_str in TRADE_CALENDAR

def get_trade_date(offset: int = 0) -> date:
    """
    获取交易日期

    Args:
        offset: 偏移天数，0=今天，-1=上一个交易日，1=下一个交易日

    Returns:
        交易日期
    """
    today = date.today()

    if offset == 0:
        if is_trade_day(today):
            return today
        else:
            return get_trade_date(-1)

    # 简单实现：向指定方向搜索
    direction = 1 if offset > 0 else -1
    current = today
    for _ in range(abs(offset) + 1):
        current += timedelta(days=direction)
        if is_trade_day(current):
            return current

    return current
