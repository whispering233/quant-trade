# Changelog

本文件记录项目的所有显著变动。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [0.0.1] - 2026-08-18

### Added

- 项目脚手架：uv + Python 3.12（src 布局）、pyproject.toml 统一配置
- 工具链：ruff（lint+format）、pyright（类型检查）、pytest、CI 工作流（ci.yml）
- 统一配置入口 `config.py`（pydantic-settings）+ `.env.example`
- 统一日志 `utils/logger.py`（控制台 + 按天滚动文件）
- 架构设计文档 `doc/design/architecture.md` 与任务清单 `doc/design/tasks.md`
- notebook 迁移至 `notebooks/`，注册 quant-trade Jupyter 内核
- 7 个业务分包占位（core/data/strategy/backtest/portfolio/risk/execution）

## Unreleased

### Added

### Changed

### Fixed

### Removed
