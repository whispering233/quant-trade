# 开发任务清单（tasks.md）

> 里程碑与任务卡片清单，按端到端功能垂直切片，尽可能细粒度、可独立验证及回滚。
> 状态图例：`[ ]` 未开始 / `[x]` 已完成

## 里程碑总览

| 里程碑 | 名称 | 目标 | 状态 |
| :--- | :--- | :--- | :--- |
| M0 | 项目初始化 | 脚手架、工具链、配置入口就绪 | ✅ 完成（v0.0.1） |
| M1 | 数据层 | akshare → sqlite → DataProvider 全链路可用 | 未开始 |
| M2 | 回测引擎 | 撮合/费用/滑点/账户/绩效，端到端回测跑通 | 未开始 |
| M3 | 策略层与 CLI | 示例策略 + 回测 CLI + 绩效输出 | 未开始 |
| M4 | 实盘扩展（预留） | portfolio / risk / execution 接口定义 | 未开始（仅接口） |

## M0 项目初始化 ✅ 已完成（2026-08-18，v0.0.1）

- 技术栈确认：uv + Python 3.12 + polars + typer + ruff + pyright + pytest + 自研回测引擎
- 脚手架：`uv init --package`（src 布局）、依赖锁定（uv.lock）、清华镜像持久化
- 工具链配置：ruff / pyright / pytest + `ci.yml`（ruff → pyright → pytest）
- `config.py` 统一配置入口（pydantic-settings）+ `.env.example`
- `utils/logger.py` 统一日志（控制台 + 按天滚动）
- notebook 迁移至 `notebooks/`，注册 quant-trade Jupyter 内核
- 7 个业务分包占位（core/data/strategy/backtest/portfolio/risk/execution）
- 冒烟验证通过：import / ruff / pyright / pytest 全绿

## M1 数据层

- [ ] `core/` 基础模型与事件定义（models / events / enums / context / exceptions）
- [ ] `doc/database` sqlite schema 设计（stock_bars / stock_list / meta）
- [ ] `storage/sqlite_store.py` K线落库与读取
- [ ] `sources/akshare_source.py` 数据源适配器
- [ ] `provider.py` DataProvider 接口 + 数据源注册表
- [ ] `scripts/fetch_data.py` 数据拉取脚本
- [ ] `test_data_pipeline.py` 集成测试（akshare→sqlite→provider）

## M2 回测引擎

- [ ] `backtest/matching.py` 撮合规则（涨跌停 / T+1 / 市价限价）
- [ ] `backtest/fee_model.py` 费用模型（佣金/印花税/过户费）
- [ ] `backtest/slippage_model.py` 滑点模型
- [ ] `backtest/account.py` SimAccount 资金/持仓/盈亏
- [ ] `backtest/broker.py` SimBroker 组装
- [ ] `backtest/engine.py` 主循环（数据→策略→撮合→记账）
- [ ] `backtest/metrics.py` 绩效指标
- [ ] 单元测试：test_matching / test_fee_model / test_account / test_metrics
- [ ] `test_backtest_flow.py` 端到端回测集成测试

## M3 策略层与 CLI

- [ ] `strategy/base.py` Strategy 抽象基类 + `signal.py`
- [ ] `strategy/registry.py` 策略注册表
- [ ] `strategy/examples/dual_ma.py` 双均线示例策略
- [ ] `strategy/examples/momentum.py` 动量示例策略
- [ ] `scripts/run_backtest.py` 回测 CLI
- [ ] 单元测试：test_strategy / test_models

## M4 实盘扩展（预留接口）

- [ ] `portfolio/oms.py` OMS 抽象（订单状态机契约）
- [ ] `portfolio/position.py` Position 管理接口
- [ ] `risk/base.py` RiskManager 抽象 + `rules.py` 规则数据类
- [ ] `execution/gateway.py` ExecutionGateway 抽象

## 演进路线（远期，未排期）

- [ ] 模拟盘模式（实时行情 + SimBroker 作为网关模拟实现）
- [ ] 参数扫描 `scripts/scan_params.py`
- [ ] 绩效可视化报告（`doc/ui`）
- [ ] 实盘网关实现（券商 API）
- [ ] 风控规则实现与熔断
