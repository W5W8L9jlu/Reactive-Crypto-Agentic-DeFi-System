# 线程测试证据

## 测试目标
- 验证状态机只能按 `PendingEntry -> ActivePosition -> Closed` 流转
- 验证 `PendingEntry` 入场 require、`ActivePosition` 出场 `minOut` 约束、`Closed` 重入拒绝

## 覆盖的场景
- happy path：not verified yet
- failure path：not verified yet
- edge case：not verified yet

## 输入
```json
{
  "intentId": "0x0000000000000000000000000000000000000000000000000000000000000001",
  "intent": {
    "owner": "0x0000000000000000000000000000000000000001",
    "inputToken": "0x0000000000000000000000000000000000000002",
    "outputToken": "0x0000000000000000000000000000000000000003",
    "plannedEntrySize": "1000000000000000000",
    "entryMinOut": "990000000000000000",
    "exitMinOutFloor": "950000000000000000"
  },
  "observedOut": "1000000000000000000",
  "runtimeExitMinOut": "950000000000000000"
}
```

## 输出
```json
{
  "status": "not verified yet",
  "events": [
    "InvestmentIntentRegistered",
    "InvestmentStateAdvanced"
  ]
}
```

## 命令
```bash
git -C D:/reactive-crypto-agentic-DeFi-system rev-parse --is-inside-work-tree
git -C D:/reactive-crypto-agentic-DeFi-system diff --name-only HEAD
git -C D:/reactive-crypto-agentic-DeFi-system log --oneline -n 10
Get-ChildItem -Path D:/reactive-crypto-agentic-DeFi-system/backend -Recurse -File | Where-Object { $_.Extension -eq '.sol' }
Get-Content D:/reactive-crypto-agentic-DeFi-system/backend/contracts/interfaces/IReactiveInvestmentCompiler.sol
Get-Content D:/reactive-crypto-agentic-DeFi-system/backend/contracts/core/ReactiveInvestmentCompiler.sol
solc --version
```

## 实际结果
- 通过：not verified yet
- 失败：`git` commands reported `not a git repository`; `solc --version` failed because `solc` is not installed
- 未覆盖：Solidity 编译、合约测试、链上回执

## 备注
- 当前工作区没有可识别的 git 仓库，且未安装 `solc`，因此没有实际测试输出可回填
