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
