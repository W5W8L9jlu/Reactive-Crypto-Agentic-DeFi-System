# 线程交付说明（更新于 2026-04-09）

## 基本信息
- 模块名: `emergency_force_close`
- Prompt 文件: `docs/prompts/emergency_force_close.prompt.md`
- Wave: `wave4`
- 负责人: `codex（待人工签收）`
- 分支: `codex/wave5`
- HEAD commit: `8e56fbd`

## 本次交付做了什么
- 在 `ReactiveInvestmentCompiler` 增加 break-glass 闭环接口：
  - `emergencyForceClose(bytes32 intentId, uint256 maxSlippageBps) returns (uint256 emergencyExitMinOut)`
- 补齐紧急权限控制能力：
  - owner 查询：`owner()`
  - relayer 授权：`setEmergencyAuthorizedRelayer` / `isEmergencyAuthorizedRelayer`
- 补齐 interface 与 runtime 调用端口：
  - `IReactiveInvestmentCompiler.sol` 新增 emergency 相关声明，ABI 对齐
  - `backend/execution/runtime/contract_gateway.py` 新增 `emergency_force_close` 与 recommendation 映射调用
- 补齐专项测试：
  - 合约层 12 条 forge 用例（含 emergency 三项最小验证）
  - runtime 集成测试覆盖 shadow recommendation -> emergency force-close

## 模块实现文件（本次相关）
- `backend/contracts/core/ReactiveInvestmentCompiler.sol`
- `backend/contracts/interfaces/IReactiveInvestmentCompiler.sol`
- `backend/contracts/test/ReactiveInvestmentCompiler.t.sol`
- `backend/execution/runtime/contract_gateway.py`
- `backend/execution/runtime/test_web3_contract_gateway_integration.py`

## 运行了哪些命令
```bash
forge test --root backend/contracts --contracts backend/contracts/core -vv
python -m unittest backend.execution.runtime.test_execution_layer backend.execution.runtime.test_web3_contract_gateway_integration -v
```

## 命令结果摘要
- `forge test ...`：`12 passed, 0 failed`
- `python -m unittest ...`：`Ran 4 tests ... OK`

## 未交付项 / 风险
- 尚无 Sepolia 真实交易回执级 smoke 证据（仅本地/测试层验证）。
- CLI 默认 wiring 尚未把 `execution force-close` 直连 runtime contract gateway。
- Mainnet 小额灰度前置（Testnet smoke）尚未完成。

## 对下游影响
- 下游可依赖 emergency ABI、权限模型与本地测试证据。
- 下游不可假设 Testnet 已验证完成，仍需先补 Sepolia smoke。
