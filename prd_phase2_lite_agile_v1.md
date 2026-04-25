# PRD-Lite：Phase 2 Core Execution Loop（敏捷 / Vibe Coding 版）

> 本文件是开发用轻量 PRD。完整版 PRD 只作为架构与安全边界参考，不作为每日开发输入。
>
> 开发时优先使用本文件中的 Sprint Goal、Story、Acceptance Criteria 和 Definition of Done。

---

## 0. 一句话目标

Phase 2 的目标是打通一个最小可用的链上条件执行闭环：

```text
TradeIntent
→ Validation
→ PreRegistrationCheck
→ ExecutionCompiler
→ registerInvestmentIntent
→ Local/Reactive Executor
→ Entry Swap
→ ActivePosition
→ StopLoss/TakeProfit Exit
→ Closed
→ ExecutionRecord + Export
```

Phase 2 不追求完整 DeFi 自动化平台，只追求单链、long-only、Uniswap V2-compatible 的可测试闭环。

---

## 1. Phase 2 MVP 范围

### 1.1 必须交付

- Pydantic v2 schema：`StrategyTemplate`、`TradeIntent`、`ExecutionPlan`、`ValidationResult`、`ExecutionRecord`。
- Validation Engine v1：模板内通过；模板外需要审批时直接中止；越界拒绝。
- PreRegistrationCheck v1：余额、allowance、TTL、gas、pair reserves、slippage、gas/profit 检查。
- Execution Compiler v1：把 `TradeIntent` 编译为链上 `InvestmentIntent` 注册载荷。
- Solidity 合约 v1：`PendingEntry -> ActivePosition -> Closed`。
- Uniswap V2-compatible entry swap。
- Stop-loss / take-profit exit swap。
- LocalExecutorAdapter：本地 / fork / testnet 触发器。
- ReactiveExecutorAdapter v1：保留真实 Reactive callback 适配位。
- ExecutionRecord：注册、入场、出场、状态、金额、tx hash。
- Export：JSON、Audit Markdown、Investment Memo。

### 1.2 明确不做

| 模块 | Phase 2 处理方式 | 后续阶段 |
|---|---|---|
| 完整 Approval Flow | `requires_manual_approval=true` 直接中止 | Phase 3 |
| Shadow Monitor daemon | 只保留 `emergencyForceClose`、事件和字段 | Phase 3 |
| Aave Protection | feature flag disabled + adapter skeleton | Phase 3.5 |
| Uniswap V3 | feature flag disabled + DexAdapter skeleton | Phase 3.5 / Phase 4 |
| Hyperlane / cross-chain | `crosschain=true` 直接拒绝 | Phase 4 |
| Webhook alerts | 只保留 `AlertSink` interface | Phase 3 |
| Postgres / Redis | 不做，默认 SQLite | 后续多用户部署 |

---

## 2. 不可违反的工程约束

1. Phase 2 只支持单链。
2. Phase 2 只支持 long-only。
3. Phase 2 只支持 Uniswap V2-compatible router。
4. Phase 2 使用注册时托管资金模型：`registerInvestmentIntent` 时转入 `tokenIn`。
5. 执行真相只来自结构化 JSON 和链上事件。
6. Audit Markdown 只能摘抄，不生成新结论。
7. Investment Memo 可以生成分析，但不能反向影响执行参数。
8. LLM 不生成 calldata，不签名，不直接控制资金。
9. PreRegistrationCheck 只做注册前链下检查，不替代链上 runtime check。
10. 合约 runtime check 是最后防线。
11. Disabled feature 必须快速失败，不能半实现接入主链路。

---

## 3. Happy Path

```text
Given 用户钱包已有 USDC，且已 approve 合约
When CLI 运行 decision dry-run / run
Then 系统生成 TradeIntent
And Validation 通过
And PreRegistrationCheck 通过
And ExecutionCompiler 生成 ExecutionPlan
And CLI 调用 registerInvestmentIntent
And 合约托管 USDC，状态为 PendingEntry
When LocalExecutor 或 Reactive callback 触发入场
And 当前价格满足 entry 条件
Then 合约 swap USDC -> WETH
And 记录 actualPositionSize
And 状态变为 ActivePosition
When 价格触发 take-profit 或 stop-loss
Then 合约 swap WETH -> USDC
And 状态变为 Closed
And ExecutionRecord 记录 register/entry/exit tx
And 可以导出 JSON / Audit Markdown / Investment Memo
```

---

## 4. 极简架构

```text
CLI
 ├─ decision run / dry-run
 ├─ execution register / show
 └─ export json / markdown / memo

Core Python
 ├─ schemas              # Pydantic truth models
 ├─ validation           # template boundary
 ├─ precheck             # RPC checks before registration
 ├─ compiler             # TradeIntent -> InvestmentIntent payload
 ├─ runtime              # tx sender + receipt parser
 ├─ event_syncer         # contract event -> ExecutionRecord
 └─ export               # JSON / Audit / Memo

Contracts
 ├─ ReactiveInvestmentCompiler.sol
 ├─ IPriceOracleAdapter.sol
 └─ UniswapV2PriceOracleAdapter.sol

Executors
 ├─ LocalExecutorAdapter
 └─ ReactiveExecutorAdapter v1
```

---

## 5. 最小数据模型

### 5.1 TradeIntent

```json
{
  "intent_id": "intent_001",
  "pair": "WETH/USDC",
  "side": "buy",
  "size_pct_nav": 0.05,
  "entry_conditions": {
    "trigger_price_max": 3050,
    "valid_until_sec": 21600
  },
  "max_slippage_bps": 80,
  "stop_loss_bps": 300,
  "take_profit_bps": 800,
  "chain_id": 1,
  "crosschain": false
}
```

### 5.2 ExecutionPlan

```json
{
  "execution_plan_id": "plan_001",
  "intent_id": "intent_001",
  "chain_id": 1,
  "register_payload": {
    "tokenIn": "USDC",
    "tokenOut": "WETH",
    "amountIn": "5000000000",
    "entryTriggerPriceE18": "3050000000000000000000",
    "entryAmountOutMinimum": "...",
    "entryValidUntil": 1711756800,
    "maxEntryGasPriceWei": "25000000000",
    "stopLossPriceE18": "2958500000000000000000",
    "takeProfitPriceE18": "3294000000000000000000",
    "stopLossSlippageBps": 80,
    "takeProfitSlippageBps": 80
  }
}
```

### 5.3 ExecutionRecord

```json
{
  "intent_id": "intent_001",
  "onchain_intent_id": "12",
  "state": "PendingEntry",
  "register_tx_hash": "0x...",
  "entry_tx_hash": null,
  "exit_tx_hash": null,
  "amount_in": "5000000000",
  "actual_position_size": null,
  "actual_exit_amount": null,
  "close_reason": null
}
```

---

## 6. Sprint Backlog

### Sprint 2.1：Schema + Validation

**Sprint Goal**  
让系统可以稳定接收、解析和拒绝非法交易意图。

**Stories**

#### S2.1-1 定义 Phase 2 schema

As a developer, I want typed Pydantic models, so that downstream modules never consume loose dicts.

Acceptance Criteria:

- `StrategyTemplate`、`TradeIntent`、`ExecutionPlan`、`ValidationResult`、`ExecutionRecord` 均为 Pydantic v2 model。
- `TradeIntent.crosschain=true` 会 validation fail。
- `TradeIntent.side != buy` 会 validation fail。
- `max_slippage_bps`、`stop_loss_bps`、`take_profit_bps` 有明确范围。
- 单元测试覆盖合法与非法样例。

#### S2.1-2 实现 Validation Engine v1

As a system, I want to compare `TradeIntent` against `StrategyTemplate`, so that only in-bound intents reach precheck.

Acceptance Criteria:

- allowed pair 通过。
- disallowed pair 拒绝。
- size 超过 `max_position_pct_nav` 拒绝。
- slippage 超过模板上限拒绝。
- 需要人工审批时 Phase 2 抛 `ApprovalRequiredError`。
- 不访问 RPC。

---

### Sprint 2.2：PreRegistrationCheck + Compiler

**Sprint Goal**  
在上链前完成链下可行性检查，并生成确定性的注册载荷。

#### S2.2-1 实现 PreRegistrationCheck v1

Acceptance Criteria:

- balance 不足抛 `InsufficientBalanceError`。
- allowance 不足抛 `InsufficientAllowanceError`。
- TTL 过期抛 `ExpiredIntentError`。
- gas 超过上限抛 `GasTooHighError`。
- reserves 读取失败抛 `ReserveUnavailableError`。
- slippage 超过上限抛 `SlippageTooHighError`。
- gas/profit 比超过阈值抛 `GasToProfitTooHighError`。
- 所有检查结果写入 `PreRegistrationCheckResult`。

#### S2.2-2 实现 Execution Compiler v1

Acceptance Criteria:

- 能从 `TradeIntent + Template + TokenMetadata` 生成 `ExecutionPlan`。
- `amountIn` 按 NAV 和 `size_pct_nav` 计算。
- `entryAmountOutMinimum` 基于 trigger price 和 slippage 计算，不依赖注册瞬间 spot price 作为唯一依据。
- `stopLossPriceE18`、`takeProfitPriceE18` 计算准确。
- USDC 6 decimals / WETH 18 decimals 测试通过。
- 输出可直接映射到合约 `InvestmentIntent`。

---

### Sprint 2.3：Contract State Machine

**Sprint Goal**  
在 fork 或 testnet 中用合约跑通注册、入场、出场状态机。

#### S2.3-1 实现 `ReactiveInvestmentCompiler.sol`

Acceptance Criteria:

- `registerInvestmentIntent` 成功托管 `tokenIn`。
- 初始状态为 `PendingEntry`。
- `executeReactiveTrigger` 在 entry 条件满足时执行 swap。
- 入场后记录 `actualPositionSize`。
- 状态转为 `ActivePosition`。
- take-profit 触发后执行 exit swap。
- stop-loss 触发后执行 exit swap。
- exit 后状态转为 `Closed`。
- `Closed` 状态重复触发必须 revert。

#### S2.3-2 实现 price adapter

Acceptance Criteria:

- `getPrice()` 返回 E18 price。
- `quoteOut()` 返回 Uniswap V2 公式估算结果。
- reserve 为 0 时 revert。
- token 顺序反转时价格仍正确。

---

### Sprint 2.4：Registration Runtime + Event Sync

**Sprint Goal**  
Python CLI 能注册 intent，并从链上事件恢复本地 ExecutionRecord。

#### S2.4-1 实现注册交易发送器

Acceptance Criteria:

- CLI 能读取 `ExecutionPlan`。
- CLI 能调用 `registerInvestmentIntent`。
- 成功后解析 `IntentRegistered` event。
- 保存 `local_intent_id -> onchain_intent_id`。
- 保存 register tx hash。

#### S2.4-2 实现 event syncer

Acceptance Criteria:

- 能同步 `EntryExecuted`。
- 能同步 `ExitExecuted`。
- 能同步 `IntentExpired` / `IntentCancelled` / `EmergencyForceClosed`。
- 重跑 sync 不产生重复记录。
- `execution show <intent-id>` 显示最新状态。

---

### Sprint 2.5：Executor + Export

**Sprint Goal**  
完成本地触发闭环和最小导出。

#### S2.5-1 实现 LocalExecutorAdapter

Acceptance Criteria:

- 本地 executor 可调用 `executeReactiveTrigger(intentId)`。
- PendingEntry 可被触发入场。
- ActivePosition 可被触发出场。
- 不满足条件时能返回清晰错误。

#### S2.5-2 实现导出

Acceptance Criteria:

- `export json <intent-id>` 输出 Machine Truth。
- `export markdown <intent-id>` 只摘抄 Machine Truth，不生成新结论。
- `export memo <intent-id>` 可生成 Investment Memo，但不影响执行 JSON。
- PendingEntry / ActivePosition / Closed 三种状态均可导出。

---

## 7. Definition of Done

Phase 2 完成的定义：

- 一个合法 `TradeIntent` 可以从 CLI 注册到合约。
- 合约成功托管 `tokenIn`。
- 本地 executor 可以触发 entry swap。
- 状态从 `PendingEntry` 变为 `ActivePosition`。
- 本地 executor 可以触发 stop-loss 或 take-profit exit。
- 状态从 `ActivePosition` 变为 `Closed`。
- Closed 后重复触发失败。
- ExecutionRecord 可通过链上事件恢复。
- JSON / Audit Markdown / Investment Memo 可导出。
- Phase 2 disabled features 均不可误触发。
- 单元测试、合约测试、最小集成测试通过。

---

## 8. Disabled Feature 测试

必须存在以下测试：

```text
test_manual_approval_required_aborts_in_phase2
test_crosschain_intent_rejected_in_phase2
test_uniswap_v3_rejected_in_phase2
test_aave_protection_not_called_in_phase2
test_webhook_alert_sink_not_required_in_phase2
test_shadow_monitor_daemon_not_required_in_phase2
```

---

## 9. Vibe Coding Task 模板

每次交给 AI coding assistant 的任务必须缩小到一个 story，不要把整份 PRD 塞进去。

```markdown
你正在实现 Phase 2 / <Story ID>。

目标：
<一句话目标>

只允许修改：
- <file path 1>
- <file path 2>

输入模型：
- <Pydantic model / Solidity struct>

必须实现：
- <function/class>

禁止实现：
- Approval Flow
- Shadow Monitor daemon
- Aave Protection
- Uniswap V3
- Cross-chain

Acceptance Criteria：
- [ ] ...
- [ ] ...

测试要求：
- <test file>
- <test cases>

完成后输出：
- 修改文件列表
- 关键设计说明
- 测试命令与结果
```

---

## 10. 第一批可直接创建的 Issue

1. `S2.1-1 Create core Pydantic schemas`
2. `S2.1-2 Implement ValidationEngine.validate_trade_intent()`
3. `S2.1-3 Add disabled feature guards`
4. `S2.2-1 Implement TokenMetadata and amount conversion helpers`
5. `S2.2-2 Implement PreRegistrationCheck balance/allowance checks`
6. `S2.2-3 Implement gas/profit check`
7. `S2.2-4 Implement ExecutionCompiler.compile()`
8. `S2.3-1 Implement InvestmentIntent storage and registration`
9. `S2.3-2 Implement entry trigger execution`
10. `S2.3-3 Implement stop-loss / take-profit exit`
11. `S2.3-4 Implement UniswapV2PriceOracleAdapter`
12. `S2.4-1 Implement register transaction sender`
13. `S2.4-2 Implement event syncer`
14. `S2.5-1 Implement LocalExecutorAdapter`
15. `S2.5-2 Implement export json/markdown/memo`

---

## 11. 当前不需要写进日常任务的内容

以下内容保留在完整版 PRD，不放进开发 prompt：

- 长篇产品定位。
- 完整三轨输出理念说明。
- Reactive Network demo 背景说明。
- Hyperlane / gasless cross-chain 远期规划。
- Aave Protection 设计展开。
- Shadow Monitor 完整 daemon 设计。
- ApprovalBattleCard 完整 UI 文案。
- 多数据源长期规划。
- 多用户部署规划。

日常开发只看：

```text
Story
Acceptance Criteria
Input / Output Model
Files allowed to modify
Tests
Disabled features
Definition of Done
```
