"""统一日志配置。

控制台输出 + 按天滚动的文件日志，格式全局统一。
业务模块通过 get_logger(__name__) 获取 logger，无需关心底层配置。

使用示例:
    from quant_trade.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.info("回测完成，共 %d 个交易日", days)
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import TimedRotatingFileHandler

from quant_trade.config import ensure_dirs, get_settings

# 统一日志格式：时间 | 级别 | 模块 | 消息
_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATEFMT = "%Y-%m-%d %H:%M:%S"

_configured = False


def _configure() -> None:
    """全局配置根 logger（幂等，只执行一次）。"""
    global _configured
    if _configured:
        return

    settings = get_settings()
    ensure_dirs()

    root = logging.getLogger()
    root.setLevel(settings.log_level.upper())
    fmt = logging.Formatter(_FORMAT, datefmt=_DATEFMT)

    # 控制台 handler
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(fmt)
    root.addHandler(console)

    # 文件 handler（按天滚动，保留 30 天）
    file_handler = TimedRotatingFileHandler(
        settings.log_dir / "quant_trade.log",
        when="midnight",
        backupCount=30,
        encoding="utf-8",
    )
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """获取项目 logger（首次调用时自动完成全局配置）。"""
    _configure()
    return logging.getLogger(name)
