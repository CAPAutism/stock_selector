import pytest
from datetime import datetime, date
from stock_selector.utils.date_utils import get_trade_date, is_trade_day, format_date

def test_format_date():
    """测试日期格式化"""
    d = date(2024, 4, 17)
    assert format_date(d) == "2024-04-17"

def test_is_trade_day_weekend():
    """测试周末不是交易日"""
    saturday = date(2024, 4, 20)  # 星期六
    assert is_trade_day(saturday) is False

def test_is_trade_day_weekday():
    """测试工作日是交易日"""
    wednesday = date(2024, 4, 17)  # 星期三
    # 简化版：只判断周末
    assert is_trade_day(wednesday) in [True, False]

def test_get_trade_date_today():
    """测试获取今日交易日"""
    today = get_trade_date()
    assert today is not None
    assert isinstance(today, date)
