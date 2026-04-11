# 线程测试证据（更新于 2026-04-09）

## 测试目标
- 验证 `emergency_force_close` 三项最小验证：
  - 权限拒绝
  - 非 `ActivePosition` 拒绝
  - force-close 后迟滞回调 revert
- 验证 runtime recommendation -> emergency force-close 映射调用。

## 执行命令（本次实测）
```bash
forge test --root backend/contracts --contracts backend/contracts/core -vv
python -m unittest backend.execution.runtime.test_execution_layer backend.execution.runtime.test_web3_contract_gateway_integration -v
```

## 关键输出
```text
Suite result: ok. 12 passed; 0 failed; 0 skipped
Ran 4 tests in 3.184s
OK
```

## 已覆盖用例（与本模块直接相关）
- `testEmergencyForceCloseOnlyOwnerOrAuthorizedRelayer`
- `testEmergencyForceCloseRejectsNonActivePosition`
- `testEmergencyForceCloseClosesBeforeAnyLateCallback`
- `test_shadow_monitor_recommendation_drives_emergency_force_close`
- `test_emergency_force_close_moves_active_position_to_closed`

## 实际结果
- 命令退出码：`0`
- Forge：`12 passed / 0 failed`
- Python runtime：`4 passed / 0 failed`

## DoD 对照
- 权限测试（owner/authorized relayer）：`verified`
- 非 `ActivePosition` 拒绝测试：`verified`
- force-close 后迟滞回调 revert：`verified`
- shadow monitor recommendation 映射 force-close：`verified（测试级）`
- Sepolia 链上 smoke：`not verified yet`

## 结论
- 本地测试层证据完整，链上 Testnet 实证仍缺失。
