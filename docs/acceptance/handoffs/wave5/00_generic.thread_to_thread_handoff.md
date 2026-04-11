# 线程间对接单
- 上游线程：`00_generic (wave5 fix-plan integration)`
- 下游线程：`cli_surface`、`shadow_monitor`、`execution_layer`、`contract adapter consumers`
- Wave：`wave5`
- handoff 日期：`2026-04-09`
- 上游 commit：`8e56fbd`（代码改动多数仍在工作树，not verified yet）

## 1. 已稳定输出（当前工作树）
- CLI 命令面（新增/对齐）：
  - `strategy create/show/edit`
  - `decision dry-run --strategy <id>`
  - `execution show/logs/force-close/fork-replay`
  - `export json/markdown/memo`
  - `monitor shadow-status`
- Runtime 紧急映射：
  - `build_emergency_force_close_call(recommendation, max_slippage_bps)`
  - `ContractGateway.emergency_force_close_from_recommendation(...)`
- 合约 emergency 接口：
  - `owner()`
  - `setEmergencyAuthorizedRelayer(address,bool)`
  - `isEmergencyAuthorizedRelayer(address)`
  - `emergencyForceClose(bytes32,uint256) returns (uint256)`

## 2. 下游必须按此消费
### 下游输入对象（recommendation）
```json
{
  "intent_id": "0x<64 hex chars>",
  "reason_code": "STOP_LOSS_BREACH | TAKE_PROFIT_BREACH | ..."
}
```

### 上游产出调用形状
```json
{
  "intent_id": "0x<64 hex chars>",
  "max_slippage_bps": 0,
  "reason_code": "string"
}
```

### 异常模型
```text
EmergencyForceCloseInputError
  - recommendation.intent_id must be non-empty str
  - recommendation.reason_code must be non-empty str
  - max_slippage_bps must be int
  - max_slippage_bps must be in [0, 10000]
  - recommendation.intent_id must be 32-byte hex string (0x...)
```

## 3. 约束
- 不允许：
  - 把 monitor recommendation 当作已签名/可直接广播交易。
  - 省略 `max_slippage_bps` 或传入越界值。
  - 使用非 bytes32 `intent_id`。
- 仅允许：
  - recommendation 作为 emergency 调用参数的候选输入。
  - 由 execution/runtime 或 CLI 执行显式 force-close 操作。
- 单位与默认值：
  - `max_slippage_bps` 单位 `bps`，范围 `[0,10000]`，默认值策略 `not verified yet`（需业务层明确）。

## 4. 示例
- sample request：
```json
{
  "recommendation": {
    "intent_id": "0x3333333333333333333333333333333333333333333333333333333333333333",
    "reason_code": "STOP_LOSS_BREACH"
  },
  "max_slippage_bps": 900
}
```
- sample response：
```json
{
  "tx_hash": "0x<hash>",
  "status": "success",
  "block_number": 1,
  "gas_used": 1
}
```
- sample failure：
```text
EmergencyForceCloseInputError: recommendation.intent_id must be 32-byte hex string (0x...)
```

## 5. 未完成项
- `backend/decision/` 与 `backend/execution/runtime/` 仍未进入已跟踪快照：`not verified yet`
- web3/anvil 集成路径（`test_web3_contract_gateway_integration.py`）本轮结果为 `3 skipped`：`not verified yet`
- `shadow_monitor -> emergency` 生产级默认 `max_slippage_bps` 策略未冻结：`not verified yet`
