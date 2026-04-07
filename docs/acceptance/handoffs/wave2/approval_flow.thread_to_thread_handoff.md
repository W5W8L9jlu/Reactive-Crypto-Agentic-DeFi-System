# approval_flow 线程间对接单

- 上游线程：`approval_flow`
- 下游线程：所有消费审批展示 / approve/reject 结果的 CLI 或编排线程
- Wave：`wave2`
- handoff 日期：`2026-04-07`
- 上游 commit：`not verified yet`

## 1. 上游已经稳定的东西
- 接口：
  - `build_approval_battle_card(...) -> ApprovalBattleCard`
  - `show_approval(..., raw=False) -> str`
  - `approve_intent(...) -> ApprovalApprovedResult`
  - `reject_intent(...) -> ApprovalRejectedResult`
  - `render_approval_battle_card(card) -> str`
- 对象：
  - `ApprovalResult`
  - `ApprovalApprovedResult`
  - `ApprovalRejectedResult`
  - `ApprovalBattleCard`
  - `DecisionMeta`
- 异常：
  - `ApprovalFlowError`
  - `ApprovalExpiredError`
  - `ApprovalBlockedError`
  - `MissingMachineTruthError`
- 命令/验证锚点：
  - `python -m unittest backend.execution.compiler.test_execution_compiler -v` -> `2 passed`
  - `python -m unittest backend.validation.test_validation_engine -v` -> `6 passed`
  - `python -m unittest backend.export.test_export_outputs -v` -> `4 passed`
  - `python -m unittest backend.cli.approval.test_approval_flow -v` -> `5 passed`

## 2. 下游必须按此消费
### 输入对象
```json
{
  "trade_intent": "TradeIntent",
  "execution_plan": "ExecutionPlan",
  "validation_result": "ValidationResult",
  "decision_meta": "DecisionMeta",
  "machine_truth_json": "string (raw show only)"
}
```

### 输出对象
```json
{
  "show_default": "Approval Battle Card text",
  "show_raw": "machine_truth_json verbatim",
  "approve": "ApprovalApprovedResult",
  "reject": "ApprovalRejectedResult"
}
```

### 异常模型
```text
ApprovalFlowError
ApprovalExpiredError
ApprovalBlockedError
MissingMachineTruthError
```

## 3. 约束
- 不允许：
  - 默认展示 raw JSON
  - 在审批模块内生成 machine truth
  - 在审批模块内执行编译或链上执行
- 仅允许：
  - 结构化对象到 battle card 的映射
  - `raw=True` 透传 machine truth
  - 过期审批阻断
- 单位与精度约定：
  - `position_usd_display` 由 `format_decimal_short(...)` 渲染
  - `*_bps` 展示由 `bps_to_percent_str(...)` 渲染
  - `entry_amount_out_minimum` 映射为字符串
- 空值/默认值约定：
  - `raw=True` 且 `machine_truth_json is None` -> `MissingMachineTruthError`
  - `is_expired=True` -> `ApprovalExpiredError`
  - `is_valid=False` -> `ApprovalBlockedError`

## 4. 示例
- sample request：
```json
{
  "trade_intent_id": "trade-001",
  "pair": "ETH/USDC",
  "dex": "uniswap-v3",
  "ttl_seconds": 300,
  "raw": false
}
```
- sample response（实测）：
  - `Approval Battle Card`
  - `TTL Remaining: 5m 0s`
  - `Approve: allowed`
- sample failure：
  - `approve_intent(...)` with expired decision meta
  - 抛出：`ApprovalExpiredError`

## 5. 未完成项
- TODO：
  - CLI route / adapter 端到端接线验证
  - 清理 battle card 映射的双实现风险（`backend/cli/models.py` vs `backend/cli/approval/flow.py`）
- 临时 workaround：
  - 使用 `show_approval` / `approve_intent` / `reject_intent` 作为当前稳定入口
- 风险提示：
  - 当前仍是未提交工作树状态，尚无 commit 级锚点
