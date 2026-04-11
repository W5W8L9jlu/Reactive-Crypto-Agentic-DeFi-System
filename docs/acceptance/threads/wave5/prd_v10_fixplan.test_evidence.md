# PRD v10 Fix-Plan 线程测试证据（2026-04-09）

## 范围
- 对照 `prd_final_v10.md` 做项目级补证与回归。
- 本轮重点：emergency 三项、动态出场最小值、dry-run/shadow/fork 命令可复现证据、风险测试缺口定位。

## 参考仓库落地（已拉取）
- `cache/reference/reactive-smart-contract-demos`
- `cache/reference/CryptoAgents`

## Fix-Plan 执行状态
- ✅ 补 emergency 三个 forge 用例：权限拒绝、非 ActivePosition 拒绝、force-close 后迟滞回调 revert。
- ✅ 动态出场最小值使用合约内推导（`actualPositionSize + slippageBps`），并有测试覆盖。
- ✅ 补 dry-run / shadow / fork 三类可复现命令入口与测试证据。
- ❌ 风险项“日亏损上限、连续亏损熔断”自动化测试仍缺（当前仓库缺少对应领域模型与业务规则落点）。

## 命令与结果
```bash
forge test --root backend/contracts --match-path test/ReactiveInvestmentCompiler.t.sol -vv
# 结果: Ran 12 tests ... 12 passed, 0 failed

python -m unittest backend.execution.compiler.test_execution_compiler backend.validation.test_validation_engine backend.export.test_export_outputs backend.reactive.adapters.test_reactive_runtime backend.cli.approval.test_approval_flow backend.cli.views.test_alerts backend.cli.test_app backend.cli.test_wiring backend.execution.runtime.test_contract_gateway backend.execution.runtime.test_execution_layer backend.execution.runtime.test_web3_contract_gateway_integration -v
# 结果: Ran 42 tests ... OK

python -m unittest backend.cli.test_app backend.cli.test_wiring -v
# 结果: Ran 11 tests ... OK
```

## Dry-Run / Shadow / Fork 复现入口（CLI 路由）
- `decision dry-run --strategy <id>`
- `monitor shadow-status`
- `execution fork-replay <intent-id> --from-block <n> --to-block <m>`

> 本轮通过 `backend/cli/test_app.py` 与 `backend/cli/test_wiring.py` 的路由测试验证三类命令已可调用并返回稳定输出。

## 高负载项对照（本轮结论）
- ✅ `entryAmountOutMinimum` 生效（entry 约束测试通过）
- ✅ `actualPositionSize` 记录（entry 后状态机记录测试通过）
- ✅ `actualPositionSize` 用于动态出场（stop-loss/take-profit 用 slippage 推导 minOut）
- ✅ `PendingEntry -> ActivePosition -> Closed` 成立
- ✅ `emergencyForceClose` 有效
- ✅ force-close 后迟滞回调 revert
- ✅ `JSON` 与 `Audit` 一致
- ✅ `ApprovalBattleCard` 数值可追溯

## 未完成项与修复方案
- ❌ 风险测试：日亏损上限、连续亏损熔断
  - 问题模块：`backend/strategy` / `backend/validation`（当前 schema 与 boundary 规则未定义 daily-loss / loss-streak 字段）
  - 修复方案：
    1. 在 `StrategyTemplate` / `StrategyIntent` 明确新增风险字段（daily loss limit、consecutive loss cap）。
    2. 在 `StrategyBoundaryService` 或专用 risk 模块实现判定规则。
    3. 补 `unittest` 用例覆盖 auto/manual/reject 三分支，并纳入统一回归命令。

## 备注
- `prd_final_v10.md` 仅阅读，未改动。
