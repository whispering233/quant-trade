# 量化交易系统架构设计文档

> 版本：v0.0.1
> 状态：M0 已实施（2026-08-18）；M1 数据层待开发

## 1. 项目背景与目标

### 1.1 定位

个人量化交易系统，以 A 股市场为主。

### 1.2 目标

- **终极目标**：完整的个人实盘交易系统（研究 → 回测 → 实盘下单全链路）
- **现阶段目标**：以研究回测为主 —— 数据获取、策略研究、回测验证
- **实盘策略**：`execution` / `risk` / `portfolio` 仅预留分包结构与接口定义，暂不实现，暂不实际下单

### 1.3 非目标（现阶段）

- 不接入实盘券商/交易所网关
- 不做实时行情推送
- 不做多用户、权限、产品化

## 2. 设计原则

| 原则 | 说明 |
| :--- | :--- |
| YAGNI | 不为没有消费者的功能建抽象；预留包只放接口，不写实现 |
| 分层混合架构 | 策略核心纯函数化，外围事件驱动壳化 |
| 回测/实盘统一 | 策略代码回测与实盘共用一份，只换数据源与执行后端 |
| 单向依赖 | 依赖方向严格单向，禁止反向依赖，保证各包可独立测试 |
| 风控独立 | 风控逻辑独立于策略层，策略 bug 不能绕过风控（预留设计） |
| A股规则收敛 | 涨跌停、T+1、费用等 A股规则全部收敛在回测撮合层，策略层不感知 |

## 3. 总体架构：分层混合架构

```
┌─────────────────────────────────────────────────┐
│ 外围：事件驱动壳（只负责"流转"）                      │
│  行情事件 → 策略回调 → 信号事件 → 订单事件 → 成交事件    │
│  回测模式：引擎按 bar 逐条喂事件（现阶段实现）           │
│  实盘模式：网关实时推送事件（预留）                     │
├─────────────────────────────────────────────────┤
│ 核心：纯函数策略层（无 IO、无隐式状态）                 │
│  signal = strategy.compute(ctx, bar)             │
│  输入输出显式数据结构，可单测、可回放、可复现             │
└─────────────────────────────────────────────────┘
```

### 3.1 回测/实盘统一机制

统一靠三层抽象：

| 抽象层 | 位置 | 作用 |
| :--- | :--- | :--- |
| ① 统一数据结构 | `core/models.py` | 回测的历史 Bar 与实盘的实时 Bar 是同一数据类 |
| ② 统一事件类型 | `core/events.py` | `BarEvent/SignalEvent/OrderEvent/FillEvent` 两模式一致 |
| ③ 统一数据入口 | `data/provider.py` | `DataProvider` 接口：回测实现 = 读本地库；实盘实现 = 实时推送 |

策略层唯一契约：

```python
class Strategy(ABC):
    def on_bar(self, ctx: StrategyContext, bar: Bar) -> Signal | None: ...
```

回测引擎与实盘引擎各自实现 `dispatch`，但喂给策略的都是同一个 `Bar`，收回的都是 `Signal`。差异被隔离在引擎内部：

- 回测：`SimBroker`（撮合）+ `SimAccount`（记账）消费信号
- 实盘（预留）：`RiskManager` → `OMS` → `ExecutionGateway` 消费信号

将来上实盘：新增 `LiveEngine` + `LiveFeed` + 实现 `execution` 包，`strategy` 与 `core` 代码零修改。

### 3.2 数据流

**回测模式（单向）**：

```
akshare（在线源）→ sqlite 缓存库（落库）→ DataProvider（读）→ 引擎（逐bar调度）
→ Strategy → Signal → SimBroker（撮合）→ SimAccount（记账）→ metrics（绩效）
```

**实盘模式（双向，预留）**：

```
交易所实时行情 → LiveFeed → LiveEngine → Strategy → Signal
→ RiskManager（校验）→ OMS（订单状态机）→ ExecutionGateway（下单）→ 交易所
→ 成交回报回流 OMS 更新持仓
```

**核心原则**：引擎不生产数据，是"数据消费者 + 调度器"。数据源决定传送带输入端（历史 vs 实时），信号消费端决定输出端（绩效 vs 真实订单）。

## 4. 分包结构

```
quant-trade/
├── pyproject.toml                  # uv 管理，统一配置入口
├── README.md / .gitignore / .env.example
├── doc/
│   ├── design/                     # 架构设计文档 + tasks.md 任务清单
│   ├── api/                        # 核心 API 设计文档（接口定稿后补）
│   ├── database/                   # sqlite 表结构设计（schema 定稿后补）
│   └── ui/                         # 可视化/报告设计（如需要）
│
├── src/quant_trade/
│   │
│   ├── __init__.py
│   ├── config.py                   # 统一配置（pydantic-settings：数据源/费用/滑点/路径）
│   │
│   ├── core/                       # ── 共享基础层：所有包依赖它，它零依赖 ──
│   │   ├── models.py               # Bar / Tick / Order / Fill / Position / Trade
│   │   ├── events.py               # BarEvent / SignalEvent / OrderEvent / FillEvent
│   │   ├── enums.py                # Direction / OrderStatus / BarPeriod / SignalType
│   │   ├── context.py              # StrategyContext：策略运行时上下文（持仓/资金/时间）
│   │   └── exceptions.py           # 自定义异常（DataNotFound / InsufficientCash...）
│   │
│   ├── data/                       # ── 数据层（现阶段实现）──
│   │   ├── provider.py             # DataProvider 抽象接口 + 数据源注册表（多源扩展点）
│   │   ├── sources/
│   │   │   ├── base.py             # DataSource 抽象：fetch(symbol, period, start, end)
│   │   │   ├── akshare_source.py   # akshare 适配器（现网源，现阶段）
│   │   │   └── sqlite_source.py    # sqlite 本地源（离线/手动导入数据，预留）
│   │   └── storage/
│   │       ├── sqlite_store.py     # K线落库/读取（拉取-缓存-读取三段分离）
│   │       └── schema.py           # 表结构：stock_bars / stock_list / meta
│   │
│   ├── strategy/                   # ── 策略层（现阶段实现）：纯函数，无IO无隐式状态 ──
│   │   ├── base.py                 # Strategy 抽象基类：on_bar(ctx, bar) -> Signal | None
│   │   ├── signal.py               # Signal：方向/标的/数量/下单类型
│   │   ├── registry.py             # 策略注册表（按名称加载，回测/扫描复用）
│   │   └── examples/
│   │       ├── dual_ma.py          # 示例：双均线
│   │       └── momentum.py         # 示例：动量突破
│   │
│   ├── backtest/                   # ── 回测引擎（现阶段实现）──
│   │   ├── engine.py               # BacktestEngine 主循环：读数据→调策略→撮合→记账（调度者）
│   │   ├── broker.py               # SimBroker（核心组件）：submit_order(Order)->Fill，接口对齐未来网关
│   │   ├── matching.py             # 撮合规则：涨跌停 / T+1 / 市价限价成交
│   │   ├── fee_model.py            # 费用模型：佣金/印花税/过户费（可配置可替换）
│   │   ├── slippage_model.py       # 滑点模型：固定/比例（可配置可替换）
│   │   ├── account.py              # SimAccount：资金/持仓/盈亏核算
│   │   └── metrics.py              # 绩效：年化/夏普/最大回撤/胜率/盈亏比
│   │
│   ├── portfolio/                  # ── 组合管理（预留：仅接口定义）──
│   │   ├── oms.py                  # OMS 抽象：订单状态机（OrderStatus 流转契约）
│   │   └── position.py             # Position 管理接口
│   │
│   ├── risk/                       # ── 风控（预留：仅接口定义）──
│   │   ├── base.py                 # RiskManager 抽象：check_order(order) -> 通过/拒绝+原因
│   │   └── rules.py                # 风控规则数据类：仓位上限/单笔限额/日亏损熔断阈值
│   │
│   ├── execution/                  # ── 执行层（预留：空包 + 接口定义，不实现）──
│   │   └── gateway.py              # ExecutionGateway 抽象：submit_order / cancel_order
│   │
│   └── utils/
│       ├── trading_calendar.py     # A股交易日历
│       └── logger.py               # 日志配置
│
├── tests/
│   ├── conftest.py
│   ├── unit/                       # test_matching / test_fee_model / test_account /
│   │                               # test_strategy / test_models / test_metrics
│   └── integration/
│       ├── test_backtest_flow.py   # 端到端：数据→策略→撮合→绩效
│       └── test_data_pipeline.py   # akshare→sqlite→provider 全链路
│
├── scripts/
│   ├── fetch_data.py               # 数据拉取：akshare → sqlite
│   ├── run_backtest.py             # 回测 CLI：--strategy --symbol --period --start --end
│   └── scan_params.py              # 参数扫描（后续里程碑）
│
└── notebooks/                      # 研究 notebook（现有 test/test.ipynb 迁入）
```

### 4.1 依赖规则（严格单向）

```
core ◄──── data ◄──── backtest
   ▲          ▲           ▲
   │          │           │
   ├──── strategy ◄───────┘      （backtest → core, data, strategy）
   │
   ├──── portfolio（预留，仅依赖 core）
   ├──── risk（预留，仅依赖 core）
   └──── execution（预留，仅依赖 core）
```

**铁律**：

- `strategy` 不得 import `data` / `backtest`
- `data` 不得 import `backtest` / `strategy`
- 预留三包现阶段只有接口文件，不得有实现
- 任何反向依赖都破坏可测性

### 4.2 各包现状

| 包 | 状态 | 现阶段交付内容 |
| :--- | :--- | :--- |
| `core` | ✅ 实现 | 数据模型、事件、枚举、异常（小而稳定） |
| `data` | ✅ 实现 | akshare 源 + sqlite 存储 + Provider 注册表 |
| `strategy` | ✅ 实现 | 基类 + 2 个示例策略 |
| `backtest` | ✅ 实现 | 完整回测：引擎/撮合/费用/滑点/账户/绩效 |
| `portfolio` | ⚠️ 仅接口 | OMS 状态机契约、Position 接口（无实现） |
| `risk` | ⚠️ 仅接口 | RiskManager 接口 + 规则数据类（无实现） |
| `execution` | ⚠️ 空包+接口 | Gateway 抽象（无实现） |

## 5. 关键接口契约（分包间"接头"）

```python
# data/provider.py —— 回测/实盘统一数据入口
class DataProvider(ABC):
    def get_bars(self, symbol: str, period: BarPeriod,
                 start: date, end: date) -> list[Bar]: ...

# data/sources/base.py —— 多数据源扩展点
class DataSource(ABC):
    def fetch(self, symbol: str, period: BarPeriod,
              start: date, end: date) -> list[Bar]: ...

# strategy/base.py —— 策略唯一契约
class Strategy(ABC):
    def on_bar(self, ctx: StrategyContext, bar: Bar) -> Signal | None: ...

# backtest/broker.py —— 对齐将来 execution/gateway.py 的接口形状
class SimBroker:
    def submit_order(self, order: Order) -> Fill | None: ...

# execution/gateway.py（预留）
class ExecutionGateway(ABC):
    def submit_order(self, order: Order) -> OrderStatus: ...
    def cancel_order(self, order_id: str) -> None: ...
```

## 6. 关键设计决策记录（ADR 摘要）

| # | 决策 | 理由 |
| :--- | :--- | :--- |
| 1 | 分层混合架构（纯函数策略核心 + 事件驱动壳） | 策略可测可复现，回测/实盘天然统一 |
| 2 | 回测/实盘共用同一份策略代码 | 避免回测实盘分叉（实盘亏钱最常见原因） |
| 3 | 数据层采用「拉取-缓存-读取」三段分离 + 注册表模式 | 数据只拉一次，回测离线可复现，多源零侵入扩展 |
| 4 | `portfolio/risk/execution` 仅接口预留 | YAGNI：现阶段无消费者，但保留实盘扩展锚点 |
| 5 | SimBroker 不单独分包，放 `backtest` 包内 | 唯一调用方是回测引擎；接口形状对齐未来 `ExecutionGateway`，将来做模拟盘时提升为网关模拟实现 |
| 6 | 撮合规则模块化（matching / fee_model / slippage_model） | 费用滑点参数扫描是研究刚需；规则可独立单测 |
| 7 | A股规则（涨跌停/T+1/费用）收敛在撮合层 | 策略层不感知市场规则差异 |
| 8 | 数据源现阶段用 akshare，预留 sqlite 本地源与多源扩展 | 免费免注册起步；本地缓存支持离线回测 |

## 7. 技术栈（已确认）

| 项 | 决策 | 说明 |
| :--- | :--- | :--- |
| 包管理 / 环境 | uv + Python 3.12 | `.python-version` 锁定版本，`uv.lock` 锁定依赖，`uv sync` 创建 `.venv` 并 editable 安装项目自身 |
| 数据处理 | polars | data 层批量处理 + metrics 统计 |
| 回测引擎 | 自研轻量引擎 | 分层混合架构，A股规则精确模拟（ADR-1/2） |
| CLI | typer | 回测/数据脚本命令行入口 |
| Lint + 格式化 | ruff | 社区标准 |
| 类型检查 | pyright | VSCode Pylance 与 CI 同一工具，配置一致 |
| 测试 | pytest | 单元 + 集成 |
| CI | GitHub Actions `ci.yml` | ruff → pyright → pytest |
| Notebook | ipykernel 内核 | `uv sync` editable 安装后，notebook 直接 `import quant_trade` |
| 项目结构 | src 布局 | `uv init --package` 生成 |

## 8. 待细化决策（后续里程碑确定）

| # | 决策点 | 确定时机 |
| :--- | :--- | :--- |
| 1 | sqlite schema 细节（stock_bars 表字段/索引） | M1 数据层，写入 `doc/database` |
| 2 | 绩效指标首批清单 | M2 回测引擎，写入 `doc/api` |
| 3 | DataProvider/DataSource 接口细节 | M1 数据层，写入 `doc/api` |
