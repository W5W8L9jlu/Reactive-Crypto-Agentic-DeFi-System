# 线程测试证据

## 测试目标
- 确认 `emergency_force_close` 所在合约改动未破坏现有状态机主路径。
- 收集 emergency 专项验证是否已存在的事实证据。

## 覆盖场景（本次实际跑到）
- `ReactiveInvestmentCompiler` 既有 8 个用例全部通过（entry/exit/closed-retrigger/constraint）。
- 这些用例覆盖普通 reactive 触发主路径与约束回退。

## 命令
```bash
forge test --root backend/contracts --contracts backend/contracts/core -vv
```

## 输入（命令上下文）
```json
{
  "root": "backend/contracts",
  "contracts_scope": "backend/contracts/core",
  "suite": "test/ReactiveInvestmentCompiler.t.sol:ReactiveInvestmentCompilerTest"
}
```

## 输出（关键结果）
```text
Compiling 3 files with Solc 0.8.33
Compiler run successful!
Ran 8 tests for ReactiveInvestmentCompilerTest
Suite result: ok. 8 passed; 0 failed; 0 skipped
```

## 实际结果
- 命令执行成功，退出码 `0`。
- 通过用例：`8`
- 失败用例：`0`
- 跳过用例：`0`

## 与模块 DoD 对照
- 权限测试（owner/authorized relayer）：`not verified yet`
- 非 `ActivePosition` 拒绝测试：`not verified yet`
- force-close 后迟滞回调 revert 测试：`not verified yet`
- 与 shadow monitor 告警联动测试：`not verified yet`

## 结论
- 已有回归测试通过，说明现有主路径未被此次改动明显破坏。
- emergency 专项最小验证未在当前测试集中看到，仍需补齐。
