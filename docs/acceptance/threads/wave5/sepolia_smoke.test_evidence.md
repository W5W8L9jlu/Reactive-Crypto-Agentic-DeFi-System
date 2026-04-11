# Sepolia 全链路 Smoke 证据（2026-04-10）

## 环境与部署

### 前置
- 已有 RPC：`SEPOLIA_RPC_URL`（或 `BASE_SEPOLIA_RPC_URL`）
- 本轮使用测试钱包私钥（会话内注入）：`SEPOLIA_PRIVATE_KEY`

### 部署命令（真实广播）
```bash
D:\Foundry\bin\forge.exe create --root . --contracts core --rpc-url $SEPOLIA_RPC_URL --private-key $SEPOLIA_PRIVATE_KEY --broadcast core/ReactiveInvestmentCompiler.sol:ReactiveInvestmentCompiler
```

### 部署结果
- Deployer: `0xAf3fDAac647cE7ED56Ba8D98bC9bF77bb768594B`
- Contract: `0x970D2B1C2d53C9bDccCf1c585CD8ddb61131D170`
- Deploy Tx: `0xd6750d47b6d5de41775ae8974b6ca5decffbd0afba41de4a77d1d2e10727074e`

---

## Smoke 执行链路

### 1) 主 smoke（含 force-close）
```bash
C:\Python314\python.exe scripts/run_sepolia_smoke.py
```

产物：
- [sepolia_smoke_20260410-045515.json](D:/reactive-crypto-agentic-DeFi-system/docs/acceptance/threads/wave5/artifacts/sepolia_smoke_20260410-045515.json)

关键结果（真实链上）：
- dry-run boundary: `manual_approval`
- approval action: `approved`
- register tx: `0xa1cec006cef14e576c31a2952df524802b5cfc7fe1778ddfbb69b4f8378ece3c`（block `10627890`）
- execute entry tx: `0x8e443f35a80f34fda99f285e581702d2eb476fa3a749adba6c95e6b51f42cc7f`（block `10627891`）
- monitor alert count: `1`
- force-close tx: `0x3241283af6dd83d70a6a47fc9ef0a0649d960fbf75c7f866b73c8f02a5820070`（block `10627892`）
- final state: `Closed`

### 2) CLI force-close 实链验证
先生成 `ActivePosition`：
```bash
C:\Python314\python.exe scripts/run_sepolia_smoke.py --skip-force-close
```

使用 CLI 执行真实 force-close：
```bash
C:\Python314\python.exe -m backend.cli.entrypoint execution force-close 0xa6ec5c7daff6ff91a4479cbd33a7c0371218b1c0666f33bdc7b456d4da621ff0
```

结果：
- tx hash: `0x01a97bc143c191245cd4f0ed8fdd28ee7ca79c1a2c5d0aef16d8e49289f666cd`
- block: `10627880`
- status: `success`

---

## 环境预检

```bash
C:\Python314\python.exe scripts/check_sepolia_smoke_env.py
```

- 结果：`Sepolia smoke env check: OK`（在设置 `SEPOLIA_PRIVATE_KEY` 与 `REACTIVE_INVESTMENT_COMPILER_ADDRESS` 后）

---

## 说明
- 本轮证据已覆盖：`dry-run -> approval -> register/execute -> export -> monitor -> force-close`
- `export` 产物（Machine Truth/Audit/Memo）已写入 smoke artifact。

---

## 复跑补充（2026-04-10 05:02 UTC）

### 执行命令（会话环境注入，不落盘）
```bash
C:\Python314\python.exe scripts/check_sepolia_smoke_env.py
C:\Python314\python.exe scripts/run_sepolia_smoke.py
```

### 本次复跑产物
- [sepolia_smoke_20260410-050227.json](D:/reactive-crypto-agentic-DeFi-system/docs/acceptance/threads/wave5/artifacts/sepolia_smoke_20260410-050227.json)

### 本次复跑关键链上结果
- register tx: `0x155fda999f88f022b82c82ae95421c51f976f18201bc885ef48debc7db11501d`
- entry tx: `0x1b2782ff65479173ef5d86e67316f22ab68b5ae71a1a4d6722d43bbc534267b9`
- force-close tx: `0x9100b4d57789c39c09aa3d10fac614a0e8ac3a62e054f8e5ba5fe431ab0c4822`
- final state: `Closed`

### CLI force-close 复跑（2026-04-10 05:05 UTC）
先生成 `ActivePosition`：
```bash
C:\Python314\python.exe scripts/run_sepolia_smoke.py --skip-force-close
```

产物：
- [sepolia_smoke_20260410-050503.json](D:/reactive-crypto-agentic-DeFi-system/docs/acceptance/threads/wave5/artifacts/sepolia_smoke_20260410-050503.json)

然后通过 CLI 路由执行 force-close：
```bash
C:\Python314\python.exe -m backend.cli.entrypoint execution force-close 0x4a5de87c92c97a434448afe322c4d9dc4a488d9706e5b96ed45612bfbb39d276
```

结果：
- tx hash: `0x0ba51cd04c0ae79da4f99374770355541763f4f33fd06fa3ea40eb96d1a978dd`
- block: `10627945`
- status: `success`
