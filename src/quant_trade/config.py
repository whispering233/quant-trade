"""统一配置入口。

所有配置通过环境变量或 .env 文件注入，pydantic-settings 负责加载与校验。
配置项按里程碑扩展：M0 只含路径与日志等基础项，
数据源/费用/滑点等配置在对应模块落地时追加。

使用示例:
    from quant_trade.config import get_settings
    settings = get_settings()
    settings.db_path  # PosixPath('data/quant_trade.db')
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """全局配置。字段均可被环境变量（前缀 QT_）或 .env 覆盖。"""

    model_config = SettingsConfigDict(
        env_prefix="QT_",
        env_file=_PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- 路径配置 ---
    data_dir: Path = _PROJECT_ROOT / "data"  # 本地数据目录（K线库、缓存）
    log_dir: Path = _PROJECT_ROOT / "logs"  # 日志目录

    # --- 日志配置 ---
    log_level: str = "INFO"  # DEBUG / INFO / WARNING / ERROR


@lru_cache
def get_settings() -> Settings:
    """获取全局配置单例（带缓存，重复调用不重复解析）。"""
    return Settings()


def ensure_dirs() -> None:
    """确保配置中涉及的目录存在（数据/日志目录）。"""
    settings = get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.log_dir.mkdir(parents=True, exist_ok=True)
