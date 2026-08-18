"""M0 冒烟测试：验证基础配置与日志可用。"""

from __future__ import annotations

from quant_trade.config import get_settings
from quant_trade.utils.logger import get_logger


def test_settings_load() -> None:
    settings = get_settings()
    assert settings.log_level.upper() in {"DEBUG", "INFO", "WARNING", "ERROR"}
    assert settings.data_dir is not None


def test_logger_works() -> None:
    logger = get_logger("test")
    logger.info("smoke test log")
    assert logger.name == "test"
