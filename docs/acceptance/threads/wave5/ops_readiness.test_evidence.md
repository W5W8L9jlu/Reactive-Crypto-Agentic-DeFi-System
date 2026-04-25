# 运维就绪度补证（2026-04-10）

## 1) `agent-cli execution force-close` 真实可用性

### 改动
- 默认 CLI 启动路径新增 runtime gateway 自动装配（按环境变量）：
  - `SEPOLIA_RPC_URL`（可选 `BASE_SEPOLIA_RPC_URL`）
  - `SEPOLIA_PRIVATE_KEY`
  - `REACTIVE_INVESTMENT_COMPILER_ADDRESS`
- `Web3InvestmentCompilerClient` 新增私钥签名发送交易路径，不再依赖节点解锁账户。
- 缺失配置时不再返回“已提交”占位文案，改为明确报错缺少哪组环境变量。

### 命令与结果
```bash
python -m backend.cli.entrypoint execution force-close intent-001
# 结果: CLI Surface Error，明确提示缺失 SEPOLIA_PRIVATE_KEY / REACTIVE_INVESTMENT_COMPILER_ADDRESS（符合当前环境事实）

python -m unittest backend.cli.test_force_close_integration -v
# 结果: Ran 2 tests ... OK（anvil 真链路，断言 tx_hash/status/block_number + 状态 Closed；含 default app 环境变量 wiring）
```

## 2) `shadow_monitor -> emergency_force_close` 集成闭环

### 命令与结果
```bash
python -m unittest backend.execution.runtime.test_web3_contract_gateway_integration -v
# 结果: Ran 3 tests ... OK

python -m unittest backend.execution.runtime.test_web3_contract_gateway_integration.Web3ContractGatewayIntegrationTestCase.test_shadow_monitor_recommendation_drives_emergency_force_close -v
# 结果: Ran 1 test ... OK
```

### `pytest -q` 的跳过说明
```bash
pytest backend/execution/runtime/test_web3_contract_gateway_integration.py -q
# 结果: 3 skipped（当前 anaconda pytest 解释器环境缺 web3/工具链）

C:\Python314\python.exe -m pytest backend/execution/runtime/test_web3_contract_gateway_integration.py -q
# 结果: 3 passed
```

## 3) 统一回归命令

已新增单命令回归脚本：
```bash
C:\Python314\python.exe scripts/run_phase1_regression.py --with-chain
```

包含：
- `unittest discover`（backend 主回归）
- `pytest` runtime web3/anvil 集成
- CLI force-close anvil 集成

## 4) 状态更新与仍未完成项（事实）

- Sepolia smoke 已完成并留档：见 [sepolia_smoke.test_evidence.md](D:/reactive-crypto-agentic-DeFi-system/docs/acceptance/threads/wave5/sepolia_smoke.test_evidence.md) 与 `artifacts/sepolia_smoke_20260410-050227.json`。
- 环境预检命令：
  - `C:\Python314\python.exe scripts/check_sepolia_smoke_env.py`
  - 在设置 `SEPOLIA_PRIVATE_KEY` 与 `REACTIVE_INVESTMENT_COMPILER_ADDRESS` 后结果：`OK`。
- CryptoAgents 真实外部 graph 运行证据未完成：
  - `C:\Python314\python.exe scripts/check_cryptoagents_graph_runtime.py`
  - 当前结果：`FAILED`（缺 `external_refs/CryptoAgents` 运行仓库或依赖）。
- Mainnet 小额灰度未启动：按 gate 要求需先完成并留档 Sepolia smoke。
- 仓库快照治理未完成：工作树仍存在大量历史 `M/??` 与生成物噪音（本轮未做破坏性清理）。

## 5) 2026-04-24 预flight结果（未注入私钥）

- 命令：`python scripts/check_sepolia_smoke_env.py`
- 结果：`FAILED`
- 事实：当前进程 env 存在 `SEPOLIA_RPC_URL` 或 `BASE_SEPOLIA_RPC_URL`，存在 `REACTIVE_INVESTMENT_COMPILER_ADDRESS`，不存在 `SEPOLIA_PRIVATE_KEY`，不存在 `REACTIVE_INVESTMENT_COMPILER_ARTIFACT`，默认 artifact 路径 `backend/contracts/out/ReactiveInvestmentCompiler.sol/ReactiveInvestmentCompiler.json` 存在。

## 6) 2026-04-24 真实链 smoke 结果（已从用户级环境注入私钥）

- 命令：
  - `python scripts/check_sepolia_smoke_env.py`
  - `python scripts/run_sepolia_smoke.py`
- 结果：`success`
- 说明：本次 smoke 运行前，已将用户级 `SEPOLIA_PRIVATE_KEY` 注入当前 shell 进程；与上一节的失败预检不是同一次环境状态。
- artifact：`docs/acceptance/threads/wave5/artifacts/sepolia_smoke_20260424-043038.json`
- register tx：`0x64483ba7a713eb178adf94f8da89d4cfb742a3563e7377192e78d171263191e0`
- entry tx：`0x01879303366426cef6d4a3ee30c5950a8e25f1d17ee2464fcd957cfc941a8729`
- force-close tx：`0x1beb88ea87fce8ed76c2f034ef040e375890993cea2509a3737108930a9898f5`
- final state：`Closed`

## 7) 2026-04-24 Shadow Monitor `shadow-status` 记录

- 命令：`python -m backend.cli.entrypoint monitor shadow-status`
- 结果：`healthy`
- tracked_intents：`1`
- critical_alerts：`0`
- checked_at：`2026-04-24T05:11:04.448328+00:00`
- source：`runtime_store`
- latest_monitor_status：`{checked_at: 2026-04-11T03:26:28.577428+00:00, status: healthy}`

## 8) 2026-04-24 关键告警触发补证

- smoke 命令：`python scripts/run_sepolia_smoke.py`
- 触发条件：`ShadowMonitor(grace_period_seconds=0)` + breached snapshot（`mark_price=2910`，`threshold_price=2950`）
- artifact：`docs/acceptance/threads/wave5/artifacts/sepolia_smoke_20260424-043038.json`
- 记录结果：
  - `monitor_alert_count: 1`
  - `force_close_recommendation_count: 1`
  - `final_state: Closed`
- 结论范围：这里只记录这次预生产 smoke 确实走到了关键告警与 force-close recommendation 路径，不延伸解释为更广泛的运维签收完成。

## 9) 2026-04-24 Phase 1 真实 RPC 门禁（Base Sepolia）

- 命令：
  - `PHASE1_GATE_NETWORK=base_sepolia python -m pytest -q backend/validation/test_phase1_real_rpc_gate.py`
- 结果：`1 passed`
- 说明：
  - `DecisionContextBuilder -> PreRegistrationCheck` 在真实 Base Sepolia RPC 上完成。
  - `Uniswap V3` 路径成功读取 `slot0 / liquidity / balanceOf / allowance`。
  - 后续补操作已执行：
    - Base Sepolia `USDC approve(spender, 200)` 成功，`tx_hash = 0x4e7f5dc93e0d253c71e22e5b13c52289a08943b6c10c4450f4752bb366dff3c5`
    - Circle Faucet（Base Sepolia）已成功发放 `20 USDC`
  - 当前钱包在该链上状态为 `wallet balance = 20`、`allowance = 200`。
  - 默认 `position_usd = 200` 下仍返回 `InsufficientBalanceError`，属于**正确拒绝**，不是假通过。
- evidence：`docs/acceptance/threads/wave5/phase1_real_rpc_gate_base_sepolia.test_evidence.md`
