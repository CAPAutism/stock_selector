import pytest
from stock_selector.config.settings import Settings

def test_settings_default_values():
    """测试默认配置值"""
    settings = Settings()
    assert settings.tushare_token is not None
    assert settings.obsidian_vault_path is not None

def test_settings_custom_values():
    """测试自定义配置值"""
    settings = Settings(
        tushare_token="test_token",
        obsidian_vault_path="/test/path"
    )
    assert settings.tushare_token == "test_token"
    assert settings.obsidian_vault_path == "/test/path"

def test_default_token_is_set():
    """测试默认Tushare token已设置"""
    settings = Settings()
    assert "bcd5ead04df2b3ccd18af6f48278c1ad038154616c47835d608c68b4" in settings.tushare_token
