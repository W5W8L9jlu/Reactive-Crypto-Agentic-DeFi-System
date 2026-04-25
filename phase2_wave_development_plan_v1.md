# Phase 2 Wave-Based Development Plan v1

适用对象：基于 CryptoAgents 的单链 DeFi 自动交易系统 Phase 2

目标：把 Phase 2 从“模块串行开发”改为“接口契约先行 + 多 Wave 并行开发 + 垂直链路集成”的执行计划，适配 vibe coding、多 AI coding agent、敏捷迭代和快速验收。

---

## 0. 执行摘要

Phase 2 不再按模块顺序开发：

```text
Validation -> PreRegistrationCheck -> Compiler -> Contract -> Runtime -> CLI -> Export
```

改为按 Wave 开发：

```text
Wave 0: Contract Freeze
Wave 1: Offline Core Loop
Wave 2: Local Chain Mock Loop
Wave 3: Fork/Testnet E2E Loop
Wave 4: Reactive + Hardening + Export Closure
```

每个 Wave 内部按 Lane 并行推进：

```text
Lane A: Schema / Validation
Lane B: Compiler / PreCheck
Lane C: Contract / Foundry
Lane D: Runtime / Event Sync
Lane E: CLI / Export
Lane F: QA / Fixtures / Docs
```

每个 Wave 的验收不是“模块完成”，而是“一个可运行增量完成”。

---

## 1. Phase 2 核心目标

Phase 2 的唯一目标：

> 打通单链 Uniswap V2-compatible 条件执行闭环。

最小闭环：

```text
TradeIntent
-> Validation Engine
-> PreRegistrationCheck
-> Execution Compiler
-> registerInvestmentIntent
-> tokenIn custody
-> PendingEntry
-> executeReactiveTrigger
-> entry swap
-> ActivePosition
-> executeReactiveTrigger
-> stop-loss / take-profit exit swap
-> Closed
-> ExecutionRecord
-> Export
```

Phase 2 的固定约束：

```text
single-chain only
long-only only
Uniswap V2-compatible only
register-time tokenIn custody
LocalExecutor first, ReactiveAdapter later
SQLite/fixture-first development
Feature flags for incomplete capabilities
```

---

## 2. Phase 2 非目标

以下内容不得进入 Phase 2 主线实现：

| 能力 | Phase 2 处理方式 | 目标阶段 |
|---|---|---|
| Approval Flow 完整审批队列 | 只返回 ApprovalRequiredError | Phase 3 |
| ApprovalBattleCard 完整交互 | 只保留 schema/stub | Phase 3 |
| Shadow Monitor daemon | 只保留合约事件、close_reason、force-close 接口 | Phase 3 |
| Webhook alerts | 只保留 AlertSink interface | Phase 3 可选 |
| Bitquery / Moralis 深度接入 | 只保留 provider skeleton | Phase 3 可选 |
| Aave Protection | 只保留 adapter skeleton | Phase 3.5 |
| Uniswap V3 | 只保留 DexAdapter 抽象 | Phase 3.5 / Phase 4 |
| Hyperlane / cross-chain | 只保留 CrosschainAdapter interface | Phase 4 |
| Postgres / Redis | 不做 | 后续部署阶段 |

---

## 3. 并行开发原则

### 3.1 Contract-first，不是 Module-first

Wave 0 必须先冻结：

```text
Pydantic schema
JSON fixtures
Solidity ABI
Solidity events
DB schema
CLI command skeleton
Feature flags
Error taxonomy
```

冻结后，各 Lane 才可以并行。

### 3.2 每个 Wave 必须有垂直集成目标

不接受“Validation 写完了”“合约写完了”这种孤立交付。

每个 Wave 必须提供一个可运行的 smoke test：

```text
Wave 1: fixture dry-run smoke
Wave 2: local mock chain smoke
Wave 3: fork/testnet smoke
Wave 4: reactive/hardening smoke
```

### 3.3 未完成能力必须 feature flag 关闭

默认配置：

```yaml
features:
  approval_flow: false
  shadow_monitor: false
  aave_protection: false
  uniswap_v3: false
  crosschain: false
  webhook_alerts: false
```

任何禁用能力被调用时，必须快速失败：

```python
raise UnsupportedFeatureError("Uniswap V3 is reserved for Phase 3.5/4")
```

---

## 4. Wave 总览

| Wave | 名称 | 目标 | 并行度 | 退出条件 |
|---|---|---|---:|---|
| W0 | Contract Freeze | 冻结 schema / ABI / events / fixtures / feature flags | 高 | 所有契约测试通过 |
| W1 | Offline Core Loop | 离线跑通 TradeIntent -> ExecutionPlan -> Export | 高 | dry-run fixture smoke 通过 |
| W2 | Local Chain Mock Loop | 本地链 + mock DEX 跑通状态机 | 高 | register -> entry -> exit -> Closed 通过 |
| W3 | Fork/Testnet E2E Loop | 真实 RPC + Uniswap V2-compatible 跑通链路 | 中高 | fork/testnet E2E 通过 |
| W4 | Reactive + Hardening | 接 Reactive adapter、幂等、异常、导出收口 | 中 | Phase 2 Definition of Done 通过 |

---

# Wave 0: Contract Freeze

## 目标

冻结并行开发所需的所有接口契约。

## 必须产出

### 0.1 Pydantic Core Schemas

目录建议：

```text
/backend/shared/schemas
  strategy_template.py
  trade_intent.py
  validation_result.py
  pre_registration_check_result.py
  execution_plan.py
  investment_intent_payload.py
  execution_record.py
  feature_flags.py
```

必须支持导出 JSON Schema：

```python
TradeIntent.model_json_schema()
ExecutionPlan.model_json_schema()
ExecutionRecord.model_json_schema()
```

### 0.2 Solidity Interface

```solidity
interface IReactiveInvestmentCompiler {
    enum IntentState {
        PendingEntry,
        ActivePosition,
        Closed,
        Cancelled,
        Expired
    }

    enum CloseReason {
        None,
        TakeProfit,
        StopLoss,
        EmergencyForceClose,
        Cancelled,
        Expired
    }

    struct InvestmentIntent {
        address owner;
        address recipient;
        address tokenIn;
        address tokenOut;
        uint256 amountIn;
        address router;
        address pair;
        address priceOracle;
        uint256 entryTriggerPriceE18;
        uint256 entryAmountOutMinimum;
        uint256 entryValidUntil;
        uint256 maxEntryGasPriceWei;
        uint256 stopLossPriceE18;
        uint256 stopLossSlippageBps;
        uint256 takeProfitPriceE18;
        uint256 takeProfitSlippageBps;
        uint256 actualPositionSize;
        uint256 actualExitAmount;
        uint256 createdAt;
        uint256 entryExecutedAt;
        uint256 closedAt;
        IntentState state;
        CloseReason closeReason;
        bool proceedsWithdrawn;
    }

    function registerInvestmentIntent(InvestmentIntent calldata intent) external returns (uint256 intentId);
    function executeReactiveTrigger(uint256 intentId) external;
    function emergencyForceClose(uint256 intentId, uint256 maxSlippageBps) external;
}
```

### 0.3 Events

```solidity
event IntentRegistered(uint256 indexed intentId, address indexed owner);
event EntryExecuted(uint256 indexed intentId, uint256 amountIn, uint256 amountOut);
event ExitExecuted(uint256 indexed intentId, uint256 positionSize, uint256 amountOut, CloseReason reason);
event IntentExpired(uint256 indexed intentId);
event IntentCancelled(uint256 indexed intentId);
event EmergencyForceClosed(uint256 indexed intentId, uint256 amountOut);
event TriggerSkipped(uint256 indexed intentId, string reason);
```

### 0.4 Fixtures

```text
/fixtures
  happy_path_strategy_template.json
  happy_path_trade_intent.json
  happy_path_execution_plan.json
  happy_path_execution_record_pending.json
  happy_path_execution_record_active.json
  happy_path_execution_record_closed.json
  rejected_crosschain_intent.json
  rejected_uniswap_v3_intent.json
  rejected_approval_required_intent.json
```

### 0.5 Error Taxonomy

```text
ValidationError
UnsupportedFeatureError
ApprovalRequiredError
InsufficientBalanceError
InsufficientAllowanceError
ExpiredIntentError
GasTooHighError
GasToProfitTooHighError
SlippageTooHighError
UnsupportedPairError
UnsupportedDexError
ContractStateError
EventSyncError
```

## 并行 Lane

| Lane | Issue | 说明 |
|---|---|---|
| A | W0-A Define Pydantic core schemas | 生成 schema 与 JSON Schema |
| B | W0-B Define InvestmentIntentPayload | Python 与 Solidity 字段一致 |
| C | W0-C Define Solidity ABI/events | interface 可 forge build |
| D | W0-D Define DB schema | ExecutionRecord / intent mapping |
| E | W0-E Define CLI skeleton | 命令存在但可 stub |
| F | W0-F Define fixtures and contract tests | fixtures 可被 pytest 读取 |

## Wave 0 Smoke Test

```bash
make test-schema
make test-fixtures
make test-feature-flags
forge build
```

## Wave 0 Exit Criteria

```text
[ ] Pydantic models 可生成 JSON Schema
[ ] fixtures 能被 schema 校验通过
[ ] Solidity interface 可编译
[ ] Python register payload 与 Solidity struct 字段一致
[ ] disabled features 默认 false
[ ] 所有 disabled feature 调用都会抛 UnsupportedFeatureError
```

---

# Wave 1: Offline Core Loop

## 目标

不访问链、不发交易、不接 Reactive，仅用 fixture 跑通离线链路：

```text
TradeIntent fixture
-> Validation Engine
-> Mock PreRegistrationCheck
-> Execution Compiler
-> ExecutionPlan
-> Audit Markdown / JSON Export
```

## 不做

```text
不访问 RPC
不签名交易
不部署合约
不接真实 Uniswap
不接真实 Reactive
不接完整 CryptoAgents
```

## 并行 Lane

| Lane | Issue | 说明 |
|---|---|---|
| A | W1-A Implement Validation Engine | 模板内通过、越界拒绝、审批中止 |
| B | W1-B Implement Execution Compiler | TradeIntent -> ExecutionPlan |
| C | W1-C Implement mock PreRegistrationCheck | 离线 mock 返回 PASSED/FAILED |
| D | W1-D Implement export from fixture | JSON / Audit Markdown |
| E | W1-E Implement CLI fixture dry-run | `agent-cli decision dry-run --fixture` |
| F | W1-F Implement offline tests | validation/compiler/export tests |

## W1-A Validation Engine Acceptance Criteria

```text
[ ] allowed pair 通过
[ ] unsupported pair 拒绝
[ ] side != buy 拒绝
[ ] crosschain=true 抛 UnsupportedFeatureError
[ ] uniswap_v3 抛 UnsupportedFeatureError
[ ] requires_manual_approval=true 抛 ApprovalRequiredError
[ ] max_slippage_bps 超模板拒绝
[ ] size_pct_nav 超模板拒绝
[ ] stop_loss_bps / take_profit_bps 越界拒绝
```

## W1-B Execution Compiler Acceptance Criteria

```text
[ ] 能计算 amountIn
[ ] 能计算 entryTriggerPriceE18
[ ] 能计算 entryAmountOutMinimum
[ ] 能计算 stopLossPriceE18
[ ] 能计算 takeProfitPriceE18
[ ] 能计算 entryValidUntil
[ ] maxEntryGasPriceWei 使用 wei，不使用 gwei 字段
[ ] USDC 6 decimals / WETH 18 decimals 测试通过
```

## W1-D Export Acceptance Criteria

```text
[ ] 能导出 ExecutionPlan JSON
[ ] 能导出 Audit Markdown
[ ] Audit Markdown 只摘抄 Machine Truth 字段
[ ] Investment Memo stub 不影响执行 JSON
```

## Wave 1 Smoke Test

```bash
agent-cli decision dry-run --fixture fixtures/happy_path_trade_intent.json
```

期望输出：

```text
ValidationResult.status = PASSED
ExecutionPlan.generated = true
Audit Markdown generated = true
No chain transaction sent
```

## Wave 1 Exit Criteria

```text
[ ] dry-run fixture smoke 通过
[ ] pytest validation/compiler/export 全绿
[ ] 无任何真实 RPC 依赖
[ ] 所有 Phase 3/4 能力保持禁用
```

---

# Wave 2: Local Chain Mock Loop

## 目标

用本地链和 Mock DEX 跑通链上状态机：

```text
registerInvestmentIntent
-> tokenIn custody
-> PendingEntry
-> LocalExecutor.executeReactiveTrigger
-> mock entry swap
-> ActivePosition
-> LocalExecutor.executeReactiveTrigger
-> mock exit swap
-> Closed
-> EventSyncer updates ExecutionRecord
```

## 不做

```text
不接真实 Uniswap
不接真实 Reactive
不接跨链
不接 Aave
不接 Shadow Monitor daemon
```

## 并行 Lane

| Lane | Issue | 说明 |
|---|---|---|
| A | W2-A Implement register with custody | transferFrom tokenIn 到合约 |
| B | W2-B Implement mock entry swap | PendingEntry -> ActivePosition |
| C | W2-C Implement mock exit swap | ActivePosition -> Closed |
| D | W2-D Implement LocalExecutor | Python 调 executeReactiveTrigger |
| E | W2-E Implement EventSyncer local logs | 解析 IntentRegistered/Entry/Exit |
| F | W2-F Implement execution show | CLI 读取 ExecutionRecord |
| G | W2-G Implement Foundry state machine tests | Solidity 测试 |

## W2-A Register Acceptance Criteria

```text
[ ] registerInvestmentIntent 成功返回 intentId
[ ] tokenIn 从 owner 转入合约
[ ] state = PendingEntry
[ ] owner / recipient / tokenIn / tokenOut 正确记录
[ ] IntentRegistered event emitted
[ ] amountIn=0 revert
[ ] unsupported router/pair revert
```

## W2-B Entry Acceptance Criteria

```text
[ ] PendingEntry 下价格满足 entryTriggerPriceE18 时可入场
[ ] quoteOut >= entryAmountOutMinimum 才能执行
[ ] block.timestamp <= entryValidUntil 才能执行
[ ] tx.gasprice <= maxEntryGasPriceWei 才能执行
[ ] 入场后 actualPositionSize > 0
[ ] state = ActivePosition
[ ] EntryExecuted event emitted
```

## W2-C Exit Acceptance Criteria

```text
[ ] ActivePosition 下达到 takeProfitPriceE18 可出场
[ ] ActivePosition 下跌破 stopLossPriceE18 可出场
[ ] 出场使用 actualPositionSize
[ ] 出场后 actualExitAmount > 0
[ ] state = Closed
[ ] closeReason = TakeProfit 或 StopLoss
[ ] ExitExecuted event emitted
[ ] Closed 状态重复触发 revert
```

## W2-E Event Syncer Acceptance Criteria

```text
[ ] 能解析 IntentRegistered
[ ] 能解析 EntryExecuted
[ ] 能解析 ExitExecuted
[ ] local_intent_id -> onchain_intent_id 映射正确
[ ] ExecutionRecord 从 PendingEntry 更新到 ActivePosition 再到 Closed
```

## Wave 2 Smoke Test

```bash
make smoke-wave-2
```

等价链路：

```text
compile fixture
-> deploy local mocks
-> approve tokenIn
-> register intent
-> execute entry
-> execute exit
-> sync events
-> execution show returns Closed
```

## Wave 2 Exit Criteria

```text
[ ] forge test 状态机用例全绿
[ ] 本地 register/entry/exit 完整链路通过
[ ] ExecutionRecord 可从事件恢复
[ ] CLI execution show 可显示状态
[ ] 无真实 Uniswap / Reactive 依赖
```

---

# Wave 3: Fork/Testnet E2E Loop

## 目标

把 Wave 2 的 mock DEX 替换成真实 RPC 与 Uniswap V2-compatible 环境。

链路：

```text
ExecutionPlan
-> PreRegistrationCheck RPC
-> registerInvestmentIntent tx
-> receipt parse
-> LocalExecutor entry
-> Uniswap V2-compatible swap
-> EventSyncer
-> LocalExecutor exit
-> EventSyncer
-> Export
```

## 不做

```text
不接 Uniswap V3
不接跨链
不接 Aave
不做完整 Approval Flow
不做 Shadow Monitor daemon
```

## 并行 Lane

| Lane | Issue | 说明 |
|---|---|---|
| A | W3-A Implement UniswapV2Adapter | router/pair/reserve/quote |
| B | W3-B Implement PriceOracleAdapter | getPrice / quoteOut |
| C | W3-C Implement RPC PreRegistrationCheck | balance/allowance/gas/reserve/slippage |
| D | W3-D Implement register tx sender | web3.py tx 构造、签名、receipt |
| E | W3-E Implement fork EventSyncer | 从真实 receipt/logs 解析 |
| F | W3-F Implement fork integration CLI | dry-run/register/show/export |
| G | W3-G Implement fork/testnet smoke | E2E 测试脚本 |

## W3-C PreRegistrationCheck Acceptance Criteria

```text
[ ] balance >= amountIn
[ ] allowance >= amountIn
[ ] entryValidUntil > now
[ ] pair reserves readable
[ ] expected slippage <= max_slippage_bps
[ ] base gas price <= max_entry_gas_price_gwei
[ ] gas_to_profit_ratio <= max_gas_to_profit_ratio
[ ] unsupported pair 拒绝
[ ] insufficient allowance 拒绝
[ ] insufficient balance 拒绝
[ ] expired intent 拒绝
```

## W3-D Register Runtime Acceptance Criteria

```text
[ ] 能从 ExecutionPlan 生成 registerInvestmentIntent calldata
[ ] 能发送 tx
[ ] 能等待 receipt
[ ] 能解析 IntentRegistered event
[ ] 能保存 onchain_intent_id
[ ] 失败时抛领域异常，不吞异常
```

## Wave 3 Smoke Test

```bash
make smoke-wave-3-fork
```

期望链路：

```text
Validation PASSED
PreRegistrationCheck PASSED
ExecutionPlan generated
register tx mined
onchain intentId parsed
LocalExecutor triggers entry
EntryExecuted synced
LocalExecutor triggers exit
ExitExecuted synced
ExecutionRecord = Closed
```

## Wave 3 Exit Criteria

```text
[ ] fork/testnet register 成功
[ ] fork/testnet entry swap 成功
[ ] fork/testnet exit swap 成功
[ ] event sync 正确
[ ] export 可从 Closed ExecutionRecord 生成
[ ] 未引入 Uniswap V3 / Aave / Cross-chain 实现
```

---

# Wave 4: Reactive + Hardening + Export Closure

## 目标

接入 ReactiveAdapter，并完成 Phase 2 收口。

链路：

```text
Wave 3 E2E
-> ReactiveAdapter trigger
-> idempotency guard
-> hardening tests
-> disabled feature tests
-> final export
-> Phase 2 Definition of Done
```

## 并行 Lane

| Lane | Issue | 说明 |
|---|---|---|
| A | W4-A Implement ReactiveAdapter v1 | 真实或 mock Reactive callback |
| B | W4-B Implement idempotency tests | 重复 callback / Closed revert |
| C | W4-C Implement hardening tests | gas/slippage/TTL/allowance/reserve |
| D | W4-D Finalize export | JSON / Audit Markdown / Memo |
| E | W4-E Finalize disabled-feature tests | approval/crosschain/V3/Aave/webhook |
| F | W4-F Write runbook and issue templates | 给 vibe coding 使用 |

## W4-A ReactiveAdapter Acceptance Criteria

```text
[ ] ReactiveAdapter 能触发 executeReactiveTrigger(intentId)
[ ] LocalExecutor 仍可作为 fallback/test path 使用
[ ] ReactiveAdapter 不做自由决策
[ ] ReactiveAdapter 不重新编译 ExecutionPlan
[ ] callback 权限符合 onlyAuthorizedExecutor 约束
```

## W4-B Idempotency Acceptance Criteria

```text
[ ] PendingEntry 重复入场不可发生
[ ] ActivePosition 重复出场不可发生
[ ] Closed 状态 executeReactiveTrigger revert
[ ] force-close 后迟滞 callback revert
[ ] EventSyncer 重复消费同一 event 不产生重复记录
```

## W4-C Hardening Acceptance Criteria

```text
[ ] entry minOut 不满足时 revert
[ ] exit minOut 不满足时 revert
[ ] entry TTL 过期时 revert
[ ] entry gas 过高时 revert
[ ] insufficient allowance 在 PreRegistrationCheck 阶段被拦截
[ ] insufficient balance 在 PreRegistrationCheck 阶段被拦截
[ ] unsupported feature 全部快速失败
```

## W4-D Export Acceptance Criteria

```text
[ ] export json 可输出 Machine Truth
[ ] export markdown 只摘抄 Machine Truth
[ ] export memo 不影响执行 JSON
[ ] registered 状态可导出
[ ] closed 状态可导出
```

## Wave 4 Smoke Test

```bash
make smoke-wave-4
```

期望：

```text
LocalExecutor happy path passes
ReactiveAdapter happy path passes
Closed repeated trigger reverts
disabled features all fail fast
export json/markdown/memo generated from same ExecutionRecord
```

## Wave 4 Exit Criteria

```text
[ ] ReactiveAdapter happy path 通过
[ ] LocalExecutor happy path 仍然通过
[ ] 幂等测试全绿
[ ] disabled feature 测试全绿
[ ] export 测试全绿
[ ] Phase 2 DoD 全部满足
```

---

## 5. Phase 2 Definition of Done

Phase 2 完成标准：

```text
[ ] CLI 能从合法 TradeIntent 生成 ExecutionPlan
[ ] Validation Engine 能判定 PASSED / REJECTED / REQUIRES_MANUAL_APPROVAL
[ ] requires_manual_approval 在 Phase 2 被中止，不上链
[ ] PreRegistrationCheck 能完成余额、allowance、gas、reserve、slippage、TTL、gas/profit 检查
[ ] Execution Compiler 能生成 InvestmentIntent 注册载荷
[ ] registerInvestmentIntent 能上链并托管 tokenIn
[ ] 状态从 PendingEntry 进入 ActivePosition
[ ] 状态从 ActivePosition 进入 Closed
[ ] EntryExecuted / ExitExecuted 事件能被同步
[ ] ExecutionRecord 能恢复链上状态
[ ] Closed 状态重复触发必须失败
[ ] LocalExecutor happy path 通过
[ ] ReactiveAdapter happy path 通过
[ ] Audit Markdown 与 Machine Truth 一致
[ ] Investment Memo 不污染执行 JSON
[ ] disabled features 不会误触发
[ ] Foundry / pytest / smoke tests 全绿
```

---

## 6. 并行开发分工建议

### Agent A: Schema / Validation

允许修改：

```text
/backend/shared/schemas
/backend/validation
/tests/validation
/fixtures
```

禁止修改：

```text
/contracts
/backend/execution/runtime
/backend/reactive
```

### Agent B: Compiler / PreCheck

允许修改：

```text
/backend/execution/compiler
/backend/execution/precheck
/tests/execution
```

禁止修改：

```text
/contracts/core
/backend/reactive
```

### Agent C: Contract / Foundry

允许修改：

```text
/contracts/interfaces
/contracts/core
/contracts/mocks
/contracts/test
```

禁止修改：

```text
/backend/validation
/backend/export
```

### Agent D: Runtime / Event Sync

允许修改：

```text
/backend/execution/runtime
/backend/execution/events
/backend/data/providers/rpc_provider.py
/tests/runtime
```

### Agent E: CLI / Export

允许修改：

```text
/backend/cli
/backend/export
/tests/export
```

### Agent F: QA / Fixtures / Docs

允许修改：

```text
/fixtures
/tests
/docs
Makefile
```

---

## 7. Issue 编号方案

建议按 Wave + Lane 编号。

```text
W0-A Define Pydantic core schemas
W0-B Define InvestmentIntentPayload
W0-C Define Solidity ABI and events
W0-D Define DB schema
W0-E Define CLI skeleton
W0-F Define fixtures

W1-A Implement Validation Engine
W1-B Implement Execution Compiler
W1-C Implement mock PreRegistrationCheck
W1-D Implement fixture export
W1-E Implement CLI dry-run fixture mode
W1-F Implement offline tests

W2-A Implement contract register with token custody
W2-B Implement mock DEX entry swap
W2-C Implement mock DEX exit swap
W2-D Implement LocalExecutor
W2-E Implement local EventSyncer
W2-F Implement execution show
W2-G Implement Foundry state machine tests

W3-A Implement UniswapV2Adapter
W3-B Implement PriceOracleAdapter
W3-C Implement RPC PreRegistrationCheck
W3-D Implement register tx sender
W3-E Implement fork EventSyncer
W3-F Implement fork integration CLI
W3-G Implement fork/testnet smoke

W4-A Implement ReactiveAdapter v1
W4-B Implement idempotency tests
W4-C Implement hardening tests
W4-D Finalize export
W4-E Finalize disabled-feature tests
W4-F Write runbook and issue templates
```

---

## 8. 推荐目录结构调整

```text
/backend
  /shared
    /schemas
    /errors.py
    /features.py
  /validation
  /execution
    /compiler
    /precheck
    /runtime
    /events
  /reactive
    /adapters
      local_executor_adapter.py
      reactive_executor_adapter.py
  /cli
  /export
/contracts
  /interfaces
    IReactiveInvestmentCompiler.sol
    IPriceOracleAdapter.sol
  /core
    ReactiveInvestmentCompiler.sol
  /mocks
    MockERC20.sol
    MockRouter.sol
    MockPriceOracleAdapter.sol
  /test
/fixtures
/tests
/docs
```

---

## 9. Makefile 建议

```makefile
test-schema:
	pytest tests/shared tests/validation -q

test-compiler:
	pytest tests/execution/test_compiler.py -q

test-runtime:
	pytest tests/runtime -q

test-export:
	pytest tests/export -q

test-contract:
	forge test

smoke-wave-1:
	agent-cli decision dry-run --fixture fixtures/happy_path_trade_intent.json

smoke-wave-2:
	pytest tests/smoke/test_wave2_local_mock.py -q

smoke-wave-3-fork:
	pytest tests/smoke/test_wave3_fork.py -q

smoke-wave-4:
	pytest tests/smoke/test_wave4_reactive.py -q

ci:
	make test-schema
	make test-compiler
	make test-runtime
	make test-export
	make test-contract
```

---

## 10. Vibe Coding Issue Card 模板

```markdown
# <Issue ID>: <Title>

## Wave
<Wave number and name>

## Goal
<One concrete implementation goal>

## Allowed Files
- path/to/file1.py
- path/to/file2.sol
- tests/path/test_file.py

## Forbidden Scope
- Do not implement Approval Flow
- Do not implement Shadow Monitor daemon
- Do not implement Aave Protection
- Do not implement Uniswap V3
- Do not implement Cross-chain
- Do not change frozen schema/ABI unless this issue explicitly says so

## Input Contract
- TradeIntent schema version: v0.1
- ExecutionPlan schema version: v0.1
- Solidity ABI version: v0.1
- Fixture: fixtures/happy_path_trade_intent.json

## Expected Output
<Describe function, CLI behavior, contract behavior, or test result>

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Tests Required
- [ ] Unit test
- [ ] Integration test if applicable
- [ ] Disabled-feature test if applicable

## Run Command
```bash
<exact command>
```
```

---

## 11. 示例 Issue Card

```markdown
# W2-B: Implement Mock DEX Entry Swap

## Wave
Wave 2: Local Chain Mock Loop

## Goal
实现 PendingEntry 状态下的 tokenIn -> tokenOut 入场，使合约能通过 MockRouter 完成 entry swap，并记录 actualPositionSize。

## Allowed Files
- contracts/core/ReactiveInvestmentCompiler.sol
- contracts/mocks/MockERC20.sol
- contracts/mocks/MockRouter.sol
- contracts/mocks/MockPriceOracleAdapter.sol
- contracts/test/ReactiveInvestmentCompilerEntry.t.sol

## Forbidden Scope
- Do not implement Uniswap V3
- Do not implement Aave Protection
- Do not implement Cross-chain
- Do not implement Shadow Monitor daemon
- Do not change IReactiveInvestmentCompiler ABI unless tests and fixtures are updated

## Input Contract
- IntentState: PendingEntry / ActivePosition / Closed / Cancelled / Expired
- CloseReason: None / TakeProfit / StopLoss / EmergencyForceClose / Cancelled / Expired
- Event: EntryExecuted(intentId, amountIn, amountOut)

## Expected Output
`executeReactiveTrigger(intentId)` 在 PendingEntry 且条件满足时完成入场，并把状态更新为 ActivePosition。

## Acceptance Criteria
- [ ] register 后 state = PendingEntry
- [ ] executeReactiveTrigger 后 state = ActivePosition
- [ ] actualPositionSize > 0
- [ ] EntryExecuted event emitted
- [ ] entryAmountOutMinimum 不满足时 revert
- [ ] entryValidUntil 过期时 revert
- [ ] Closed 状态不能重复 entry

## Tests Required
- [ ] test_entry_success
- [ ] test_entry_reverts_when_min_out_not_met
- [ ] test_entry_reverts_when_expired
- [ ] test_entry_reverts_when_closed

## Run Command
```bash
forge test --match-contract ReactiveInvestmentCompilerEntryTest
```
```

---

## 12. 合并规则

每个 PR 必须满足：

```text
[ ] 对应 issue 的 acceptance criteria 全部勾选
[ ] 有测试
[ ] 不破坏 fixture
[ ] 不打开 Phase 3/4 feature flag
[ ] 不引入未授权外部依赖
[ ] 不修改冻结契约；如必须修改，必须同步更新 schema、ABI、fixture、tests
[ ] smoke test 不回退
```

---

## 13. 契约变更规则

冻结契约包括：

```text
/backend/shared/schemas/*.py
/contracts/interfaces/*.sol
/fixtures/*.json
/backend/shared/errors.py
/config/features.yaml
```

修改任何冻结契约，必须同步更新：

```text
schema tests
compiler tests
contract tests
event syncer tests
export tests
fixtures
README / wave docs
```

否则不得合并。

---

## 14. 推荐开发节奏

```text
Day 1-2: Wave 0
Day 3-5: Wave 1
Day 6-10: Wave 2
Day 11-15: Wave 3
Day 16-20: Wave 4
```

这是理想节奏。实际开发可以按风险调整：

```text
合约风险高 -> 延长 Wave 2
RPC/Uniswap 风险高 -> 延长 Wave 3
Reactive 风险高 -> Wave 4 先用 mock reactive，再接真实 adapter
```

---

## 15. 管理视角看板

建议看板列：

```text
Backlog
Ready for Wave
In Progress
Blocked by Contract
Blocked by Runtime
Needs Integration
Smoke Testing
Done
```

建议标签：

```text
wave:0-contract-freeze
wave:1-offline
wave:2-local-chain
wave:3-fork-e2e
wave:4-reactive-hardening
lane:schema
lane:compiler
lane:contract
lane:runtime
lane:cli-export
lane:qa
risk:abi-change
risk:external-integration
feature-disabled
```

---

## 16. 关键风险与处理

| 风险 | 处理 |
|---|---|
| schema 与 Solidity struct 漂移 | Wave 0 冻结契约，CI 校验 fixture |
| 多 AI agent 改同一文件 | issue card 限制 allowed files |
| 半成品功能误入主链路 | feature flag 默认 false + disabled-feature tests |
| Reactive 集成阻塞 | LocalExecutor 先跑通，Reactive 放 Wave 4 |
| Uniswap 真实环境排障困难 | Wave 2 先 mock DEX，Wave 3 再 fork/testnet |
| event sync 重复消费 | W4 增加幂等测试 |
| 合约 ABI 频繁变化 | ABI 变更必须同步 Python payload、fixtures、tests |

---

## 17. 外部参考

- Scrum Guide: Sprint Backlog 由 Sprint Goal、选入的 Product Backlog Items 和交付 Increment 的可执行计划组成。
- Pydantic Docs: BaseModel.model_json_schema 可生成 JSON Schema。
- Foundry Forge Docs: Forge 用于编译、测试和部署 Solidity 合约，并支持测试、trace、fork-based workflows。
- Martin Fowler: Feature Toggles / Feature Flags 可支持持续交付下的未完成能力隔离。

---

## 18. 最终建议

Phase 2 的开发主控文档应从“模块清单”变成“Wave 集成计划”。

推荐实际使用顺序：

```text
大 PRD = 架构参考
PRD-Lite = 产品边界
Wave Plan = 开发主控
Issue Card = 每次 vibe coding 输入
Fixture = 接口真相
Tests = 验收真相
```

每次 vibe coding 不要喂完整 PRD，只喂：

```text
当前 Wave 目标
当前 Issue Card
相关 schema / ABI
相关 fixture
禁止实现列表
Acceptance Criteria
Run Command
```

这样可以最大化并行开发速度，同时避免 Phase 3 / Phase 4 的复杂能力提前污染 Phase 2 主链路。
