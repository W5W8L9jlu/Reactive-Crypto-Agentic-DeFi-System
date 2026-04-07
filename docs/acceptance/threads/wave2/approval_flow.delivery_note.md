# approval_flow 线程交付说明

## 基本信息
- 模块名：`approval_flow`
- Prompt 文件：`docs/prompts/approval_flow.prompt.md`
- Wave：`wave2`
- 负责人：`not verified yet`
- 分支：`w1-gate-fail-fix`
- commit：`not verified yet`

## 本次交付做了什么
- 交付审批展示与分流：
  - `render_approval_battle_card(card) -> str`
  - `show_approval(...)`
  - `approve_intent(...)`
  - `reject_intent(...)`
- 交付审批错误模型与结果模型：
  - `ApprovalFlowError`、`ApprovalExpiredError`、`ApprovalBlockedError`、`MissingMachineTruthError`
  - `ApprovalResult`、`ApprovalApprovedResult`、`ApprovalRejectedResult`
- 恢复 `execution_compiler` 冻结基线，解除 `approval_flow` 导入阻塞：
  - `models.py`（含 `RegisterPayload` / alias 字段）
  - `compiler.py`（`compile_execution_plan`、`freeze_contract_call_inputs`）
  - `__init__.py`、`errors.py`
  - `test_execution_compiler.py`

## 修改了哪些文件
- `backend/cli/views/approval_battle_card.py`
- `backend/cli/approval/__init__.py`
- `backend/cli/approval/errors.py`
- `backend/cli/approval/flow.py`
- `backend/cli/approval/test_approval_flow.py`
- `backend/execution/compiler/models.py`
- `backend/execution/compiler/compiler.py`
- `backend/execution/compiler/__init__.py`
- `backend/execution/compiler/errors.py`
- `backend/execution/compiler/test_execution_compiler.py`

## 没做什么
- 没有在审批模块内生成 machine truth
- 没有把执行编译逻辑迁入审批模块
- 没有做链上执行
- 没有完成 CLI route / adapter 端到端接线验证

## 运行了哪些命令
```bash
python -m unittest backend.execution.compiler.test_execution_compiler -v
python -m unittest backend.validation.test_validation_engine -v
python -m unittest backend.export.test_export_outputs -v
python -m unittest backend.cli.approval.test_approval_flow -v
@'
# python inline: construct TradeIntent/ExecutionPlan/DecisionMeta and call show_approval(...)
'@ | python -
```

## 验收证据
- 测试截图：`not verified yet`
- 日志（关键结果）：
  - compiler: `Ran 2 tests ... OK`
  - validation: `Ran 6 tests ... OK`
  - export: `Ran 4 tests ... OK`
  - approval_flow: `Ran 5 tests ... OK`
- 示例 payload：
  - `TradeIntent(trade_intent_id="trade-001", pair="ETH/USDC", ttl_seconds=300, ...)`
  - `RegisterPayload(intentId="intent-001", entryAmountOutMinimum=1450000000, ...)`
  - `DecisionMeta(trade_intent_id="trade-001", ttl_seconds=300, ...)`
- 示例输出（实测）：
  - `Approval Battle Card`
  - `TTL Remaining: 5m 0s`
  - `Approve: allowed`

## 对下游线程的影响
- 稳定输入：
  - `TradeIntent`
  - `ExecutionPlan`
  - `ValidationResult`
  - `DecisionMeta`
  - `machine_truth_json`（仅 raw 展示）
- 稳定输出：
  - `ApprovalBattleCard`
  - 审批文本视图
  - `ApprovalApprovedResult`
  - `ApprovalRejectedResult`
- 稳定异常：
  - `ApprovalFlowError`
  - `ApprovalExpiredError`
  - `ApprovalBlockedError`
  - `MissingMachineTruthError`
- 需要下游同步：
  - 继续使用 compiler 的 alias 字段面（`intentId` / `entryAmountOutMinimum` 等）与冻结映射
