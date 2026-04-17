import pytest
from unittest.mock import patch, MagicMock
from stock_selector.data_sources.tushare_client import TushareClient

def test_tushare_client_init():
    """测试Tushare客户端初始化"""
    client = TushareClient(token="test_token")
    assert client.token == "test_token"

@patch('stock_selector.data_sources.tushare_client.ts')
def test_get_sector_fund_flow_mock(mock_ts):
    """测试获取板块资金流向(模拟)"""
    mock_api = MagicMock()
    mock_ts.pro_api.return_value = mock_api
    mock_ts.set_token.return_value = None
    mock_df = MagicMock()
    mock_df.empty = False
    mock_api.ths_dp.return_value = mock_df

    client = TushareClient(token="test_token")
    result = client.get_sector_fund_flow("20240417")
    mock_api.ths_dp.assert_called_once()