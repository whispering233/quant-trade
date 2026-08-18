# quant-trade

A股个人量化交易系统 —— 分层混合架构，回测/实盘共用同一份策略代码。

> 当前阶段：研究回测为主（v0.0.1）；实盘扩展（组合管理/风控/执行）仅预留接口，暂不实际下单。

## 特性

- **分层混合架构**：纯函数策略核心 + 事件驱动外围壳，策略可单测、可回放、可复现
- **回测/实盘统一**：策略只认统一的 Bar 数据与事件，将来上实盘无需修改策略代码
- **A股规则精确模拟**：涨跌停、T+1、佣金/印花税/过户费、滑点模型（回测撮合层）
- **数据拉取-缓存-读取三段分离**：akshare 在线拉取 → sqlite 本地缓存 → 统一读取，离线可复现回测
- **多数据源可扩展**：DataSource 注册表模式，新增数据源零侵入

## 技术栈

| 项 | 选型 |
| :--- | :--- |
| 语言 / 环境 | Python 3.12 · uv（`.python-version` + `uv.lock` 锁定） |
| 数据处理 | polars |
| 回测引擎 | 自研轻量事件驱动引擎 |
| CLI | typer |
| 代码质量 | ruff（lint+format）· pyright（类型检查）· pytest |
| CI | GitHub Actions（ruff → pyright → pytest） |

## 快速开始

```bash
uv sync                      # 安装依赖（自动创建 .venv）
uv run pytest                # 运行测试
uv run python -c "import quant_trade; print(quant_trade.__version__)"
```

Notebook 研究：VSCode 打开 `notebooks/`，内核选择 **Python (quant-trade)**。

## 目录结构

```
src/quant_trade/
├── core/        # 共享基础：数据模型、事件、枚举（零依赖）
├── data/        # 数据层：akshare 源 + sqlite 存储 + DataProvider
├── strategy/    # 策略层：纯函数策略（回测/实盘共用）
├── backtest/    # 回测引擎：撮合 / 费用 / 滑点 / 账户 / 绩效
├── portfolio/   # 组合管理（预留接口）
├── risk/        # 风控（预留接口）
├── execution/   # 执行层（预留接口）
└── utils/       # 日志等工具
doc/             # design（架构设计/任务清单）/ api / database / ui
```

## 文档

- [系统架构设计](doc/design/architecture.md)
- [开发任务清单](doc/design/tasks.md)
- [变更日志](CHANGELOG.md)

## 演进路线

M1 数据层 → M2 回测引擎 → M3 策略与 CLI → M4 实盘扩展接口（模拟盘 → 实盘网关）。
