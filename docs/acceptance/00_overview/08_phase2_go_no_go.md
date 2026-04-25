# Phase 2 Go / No-Go 验收清单

> 用于判断 Phase 2 是否完成 Core Execution Loop，并可进入 Phase 3 Control Plane + Operational Safety。  
> Phase 2 不以“模块完成”作为 GO 标准，只以单链、long-only、Uniswap V2-compatible 条件执行闭环是否闭合作为 GO 标准。

## 0. 基本信息

- 评估日期：
- 评估人：
- 评估范围：Phase 2 / Core Execution Loop
- 结论口径：可进入 Phase 3 / 继续 Phase 2 补齐

## 1. Phase 2 固定边界

- [ ] 仅支持 single-chain。
- [ ] 仅支持 long-only。
- [ ] 仅支持 Uniswap V2-compatible router / pair。
- [ ] 仅支持 register-time `tokenIn` custody。
- [ ] LocalExecutor 先跑通，ReactiveExecutorAdapter v1 后接入。
- [ ] SQLite / fixture-first，不引入 Postgres / Redis。
- [ ] disabled features 默认关闭并快速失败。

## 2. Core Execution Loop 门禁

Phase 2 GO 必须证明以下路径完整闭合：

```text
TradeIntent
-> Validation
-> PreRegistrationCheck
-> ExecutionCompiler
-> registerInvestmentIntent
-> tokenIn custody
-> PendingEntry
-> executeReactiveTrigger
-> entry swap
-> ActivePosition
-> executeReactiveTrigger
-> stop-loss / take-profit exit swap
-> Closed
-> EventSyncer
-> ExecutionRecord
-> JSON / Audit Markdown / Investment Memo export
```

验收项：

- [ ] `TradeIntent` 使用 Pydantic v2 truth model。
- [ ] Validation Engine 拒绝越界 pair / side / size / slippage / disabled feature。
- [ ] `requires_manual_approval == true` 在 Phase 2 直接中止。
- [ ] PreRegistrationCheck 基于 RPC 真相完成 balance / allowance / TTL / gas / reserves / slippage / gas-profit 检查。
- [ ] ExecutionCompiler 只在注册时编译，触发时不重编译。
- [ ] `registerInvestmentIntent` 成功托管 `tokenIn`。
- [ ] 入场触发后状态从 `PendingEntry` 进入 `ActivePosition`。
- [ ] stop-loss / take-profit 触发后状态进入 `Closed`。
- [ ] `Closed` 状态禁止重复执行。
- [ ] EventSyncer 可从合约事件恢复 `ExecutionRecord`。
- [ ] Export 可输出 JSON / Audit Markdown / Investment Memo，且 Audit 只摘抄 Machine Truth。

## 3. Wave Gate 门禁

- [ ] `P2_W0.wave_gate.md` 通过：Interface Freeze。
- [ ] `P2_W1.wave_gate.md` 通过：Offline Core Loop。
- [ ] `P2_W2.wave_gate.md` 通过：Local Chain Mock Loop。
- [ ] `P2_W3.wave_gate.md` 通过：Fork/Testnet E2E Loop。
- [ ] `P2_W4.wave_gate.md` 通过：Reactive + Hardening + Export Closure。

## 4. Disabled Feature 门禁

以下能力不得进入 Phase 2 主链路：

- [ ] complete Approval Flow queue 快速失败或未接入。
- [ ] Shadow Monitor daemon 不阻塞 Phase 2 GO。
- [ ] Aave Protection 默认禁用。
- [ ] Uniswap V3 默认禁用。
- [ ] cross-chain / Hyperlane 默认禁用。
- [ ] webhook alerts 默认禁用。
- [ ] Postgres / Redis 不进入 Phase 2 默认路径。

## 5. 不变量核对

- [ ] AI 不直接生成最终 calldata。
- [ ] AI 不签名。
- [ ] AI 不直接控制资金。
- [ ] 执行真相来自结构化 JSON 与链上事件。
- [ ] 执行层只信 RPC，不信第三方索引 API。
- [ ] Reactive 仅做事件驱动、条件触发和 callback，不做自由策略决策。
- [ ] 合约 runtime check 是最后防线。
- [ ] Audit Markdown 只摘抄，不生成新结论。
- [ ] Investment Memo 不反向影响执行参数。

## 6. 证据命令（建议）

```powershell
python scripts/workflow.py audit-manifest --strict
python scripts/workflow.py check validation_engine --execute --strict
python scripts/workflow.py check pre_registration_check --execute --strict
python scripts/workflow.py check execution_compiler --execute --strict
python scripts/workflow.py check execution_layer --execute --strict
python scripts/workflow.py check reactive_runtime --execute --strict
python scripts/workflow.py check export_outputs --execute --strict
python scripts/workflow.py check --all --execute --strict
```

Wave smoke 证据必须写入：

```text
docs/acceptance/threads/phase2_wave0/
docs/acceptance/threads/phase2_wave1/
docs/acceptance/threads/phase2_wave2/
docs/acceptance/threads/phase2_wave3/
docs/acceptance/threads/phase2_wave4/
```

## 7. 判定

- `GO`：Core Execution Loop 闭合，W0-W4 gates 通过，disabled features 快速失败，三轨导出一致。
- `HOLD`：部分 Wave 通过，但 E2E / Reactive / export closure 证据不完整。
- `FAIL`：违反核心不变量，触发时重编译，AI 生成 calldata，或 disabled feature 进入主链路。

## 8. 最终签字

- 结论：
- 主要阻塞项：
- 风险接受项：
- 签字人：
- 日期：
