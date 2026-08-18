# AGENTS.md — 项目指南（供 AI 助手与开发者阅读）

## 项目简介

quant-trade：A股个人量化交易系统。分层混合架构（纯函数策略核心 + 事件驱动外围壳），
回测/实盘共用同一份策略代码。现阶段以研究回测为主，实盘扩展（portfolio/risk/execution）仅预留接口。

## 常用命令

```bash
uv sync                 # 按 uv.lock 同步虚拟环境
uv run python -c "..."  # 在项目环境中执行
uv run pytest           # 运行测试
uv run ruff check .     # 代码规范检查
uv run ruff format .    # 代码格式化
uv run pyright          # 类型检查
uv run jupyter lab      # 启动 notebook（内核：Python (quant-trade)）
```

- Python 版本锁定：`.python-version`（3.12）
- 依赖锁定：`uv.lock`（提交 git）；新增依赖用 `uv add`，不要手改 lock
- PyPI 镜像已配置清华源（`[[tool.uv.index]]`），CI 环境自动覆盖回官方源

## 目录结构

```
src/quant_trade/
├── core/        # 共享基础层：models / events / enums / context / exceptions（零依赖）
├── data/        # 数据层：sources（akshare 等）+ storage（sqlite）+ provider（统一入口）
├── strategy/    # 策略层：纯函数，on_bar(ctx, bar) -> Signal | None（回测/实盘共用）
├── backtest/    # 回测引擎：engine / broker(SimBroker) / matching / fee_model / slippage_model / account / metrics
├── portfolio/   # 组合管理（预留接口）：OMS 订单状态机
├── risk/        # 风控（预留接口）：RiskManager
├── execution/   # 执行层（预留接口）：ExecutionGateway
└── utils/       # 日志等基础工具
doc/design/      # 架构设计文档（architecture.md）与任务清单（tasks.md）
doc/api/         # 核心 API 设计文档（按模块）
doc/database/    # 数据结构 schema 设计
tests/           # 单元 + 集成测试
scripts/         # 数据拉取、回测 CLI
notebooks/       # 研究 notebook
```

## 架构铁律

1. 依赖严格单向：`strategy` 不得 import `data/backtest`；`data` 不得 import `backtest`；预留三包仅依赖 `core`
2. 策略代码必须是纯函数风格：无 IO、无隐式状态，输入输出显式
3. A股规则（涨跌停/T+1/费用）收敛在 `backtest` 撮合层，策略层不感知
4. 回测/实盘统一：策略只认 `core` 的 Bar 数据结构与事件，不认数据来源
5. SimBroker 接口形状对齐将来的 `ExecutionGateway`（`submit_order(Order) -> Fill`）

## 开发规范

- 遵循 `doc/design/` 下设计文档；改架构先更新文档再改代码
- 功能开发顺序：讨论 → 更新 doc/design → 更新 tasks.md → 实现 → 验证 → 清理任务清单
- 提交信息规范：`M{x}: 描述`（里程碑）或 `chore: 描述` / `fix: 描述`
- 版本发布：更新 CHANGELOG.md → 打 tag（`vX.Y.Z`）→ push tag 自动触发 GitHub Release
