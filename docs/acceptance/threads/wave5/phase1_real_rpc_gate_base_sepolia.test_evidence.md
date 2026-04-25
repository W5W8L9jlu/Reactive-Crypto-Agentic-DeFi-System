# Phase 1 真实 RPC 门禁证据（Base Sepolia）

## 目标
- 验证 `DecisionContextBuilder -> PreRegistrationCheck` 在真实 Base Sepolia RPC 上可运行。
- 验证 Uniswap V3 路径可读取 `slot0 / liquidity / balanceOf / allowance`。
- 验证门禁在真实链状态不满足时，会按规则明确拒绝，而不是假通过。

## 配置
- `PHASE1_GATE_NETWORK=base_sepolia`
- `BASE_SEPOLIA_RPC_URL`：会话环境已存在
- 默认地址来自测试内置映射：
  - `PHASE1_GATE_WALLET_ADDRESS = 0xAf3fDAac647cE7ED56Ba8D98bC9Bf77bb768594B`
  - `PHASE1_GATE_INPUT_TOKEN_ADDRESS = 0x036CbD53842c5426634e7929541eC2318f3dCF7e`
  - `PHASE1_GATE_OUTPUT_TOKEN_ADDRESS = 0x4200000000000000000000000000000000000006`
  - `PHASE1_GATE_POOL_ADDRESS = 0x46880b404CD35c165EDdefF7421019F8dD25F4Ad`
  - `PHASE1_GATE_ALLOWANCE_SPENDER_ADDRESS = 0x492E6456D9528771018DeB9E87ef7750EF184104`

## 命令
```powershell
$env:PHASE1_GATE_NETWORK='base_sepolia'
python -m pytest -q D:\reactive-crypto-agentic-DeFi-system\backend\validation\test_phase1_real_rpc_gate.py
```

## 实际结果
- 结果：`1 passed`
- 耗时：约 `47.45s`（最近一次）
- `DecisionContextBuilder` 成功读取真实 Base Sepolia 链状态。
- `PreRegistrationCheck` 真实执行并返回 `InsufficientBalanceError`。

## 关键事实
- 读取到的池子/链状态证明 V3 路径有效。
- 2026-04-24 补充操作：
  - 已在 Base Sepolia 上成功执行 `USDC approve(spender, 200)`：
    - `tx_hash = 0x4e7f5dc93e0d253c71e22e5b13c52289a08943b6c10c4450f4752bb366dff3c5`
  - 已在 Circle Faucet 上选择 `Base Sepolia` 并成功发放一笔 `20 USDC`。
- 该钱包当前 Base Sepolia 状态：
  - `wallet balance = 20`
  - `allowance = 200`
- 因默认 `position_usd = 200`，余额仍不足，门禁继续**正确拒绝**（`InsufficientBalanceError`）。

## 结论
- 这次 Base Sepolia 门禁已完成真实链路验证。
- 结果是“通路可用，授权已满足，但默认仓位下真实余额仍不满足放行条件”。
- 这条证据不能替代 Sepolia 主线证据，只能证明同类链路在 Base Sepolia 上可运行。
