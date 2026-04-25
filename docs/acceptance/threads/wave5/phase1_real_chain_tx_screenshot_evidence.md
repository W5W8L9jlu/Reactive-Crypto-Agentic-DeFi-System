# Phase1 真实链交易截图证据（2026-04-24）

## 目标
- 固化本轮为通过 `Phase1 real rpc gate` 所执行的 3 笔 Sepolia 真实链交易证据。
- 同时保留浏览器截图证据（Sepolia Etherscan）与 RPC 读数证据（receipt + 余额/allowance）。

---

## 证据范围
- 网络：`Sepolia`（`chain_id = 11155111`）
- 钱包：`0xAf3fDAac647cE7ED56Ba8D98bC9bF77bb768594B`
- 交易：
1. swap #1：`ETH -> USDC`（小额探测）
2. swap #2：`ETH -> USDC`（补足 gate 所需余额）
3. approve：`USDC approve(spender, max)`（补足 allowance）

---

## 浏览器截图证据（Sepolia Etherscan）

### 1) swap #1
- tx: `0x2ecf681afd170c9c234a5166e595425b6f466db3069882cf21590d87ad822dd4`
- Etherscan: [查看交易](https://sepolia.etherscan.io/tx/0x2ecf681afd170c9c234a5166e595425b6f466db3069882cf21590d87ad822dd4)
- 本地截图：
  - [0x2ecf681afd170c9c234a5166e595425b6f466db3069882cf21590d87ad822dd4.png](D:/reactive-crypto-agentic-DeFi-system/docs/acceptance/threads/wave5/screenshots/2026-04-24-phase1-real-chain/0x2ecf681afd170c9c234a5166e595425b6f466db3069882cf21590d87ad822dd4.png)

### 2) swap #2
- tx: `0x29aa59dff338af035963ce636a9837a7745b4277d3de46a64d984454e439d538`
- Etherscan: [查看交易](https://sepolia.etherscan.io/tx/0x29aa59dff338af035963ce636a9837a7745b4277d3de46a64d984454e439d538)
- 本地截图：
  - [0x29aa59dff338af035963ce636a9837a7745b4277d3de46a64d984454e439d538.png](D:/reactive-crypto-agentic-DeFi-system/docs/acceptance/threads/wave5/screenshots/2026-04-24-phase1-real-chain/0x29aa59dff338af035963ce636a9837a7745b4277d3de46a64d984454e439d538.png)

### 3) approve
- tx: `0xf35efaeb6337ee04267192d8c586bd77b6f310b1db9ea7ca15d8e6188c4f796f`
- Etherscan: [查看交易](https://sepolia.etherscan.io/tx/0xf35efaeb6337ee04267192d8c586bd77b6f310b1db9ea7ca15d8e6188c4f796f)
- 本地截图：
  - [0xf35efaeb6337ee04267192d8c586bd77b6f310b1db9ea7ca15d8e6188c4f796f.png](D:/reactive-crypto-agentic-DeFi-system/docs/acceptance/threads/wave5/screenshots/2026-04-24-phase1-real-chain/0xf35efaeb6337ee04267192d8c586bd77b6f310b1db9ea7ca15d8e6188c4f796f.png)

---

## RPC 读数证据（同一钱包、同一网络）

### receipt 关键字段
| tx_hash | status | block_number | from | to | gas_used | value_wei |
|---|---:|---:|---|---|---:|---:|
| `0x2ecf681afd170c9c234a5166e595425b6f466db3069882cf21590d87ad822dd4` | 1 | 10722041 | `0xAf3f...594B` | `0x3bFA...Ae48E` | 114486 | 1000000000000000 |
| `0x29aa59dff338af035963ce636a9837a7745b4277d3de46a64d984454e439d538` | 1 | 10722045 | `0xAf3f...594B` | `0x3bFA...Ae48E` | 123188 | 120000000000000000 |
| `0xf35efaeb6337ee04267192d8c586bd77b6f310b1db9ea7ca15d8e6188c4f796f` | 1 | 10722047 | `0xAf3f...594B` | `0x1c7D...7238` | 55785 | 0 |

### swap 产出（USDC Transfer 到钱包）
- tx `0x2ecf...2dd4`：`8.216497 USDC`
- tx `0x29aa...d538`：`985.226788 USDC`

### 执行后状态（USDC + allowance）
- `USDC balanceOf(wallet)` = `1033443285`（`1033.443285 USDC`）
- `allowance(wallet, spender)` =  
  `115792089237316195423570985008687907853269984665640564039457584007913129639935`（max uint256）

---

## 交易作用解释
1. `swap #1`：先用小额 ETH 验证该 router/pool 路径可达，拿到第一笔 USDC。
2. `swap #2`：继续换入 USDC，把钱包 USDC 提升到可覆盖当前 gate `position_usd` 的区间。
3. `approve`：把 USDC 对 gate spender 的授权补到充分值（max），避免 `InsufficientAllowanceError`。

结论：上述 3 笔交易后，`wallet_input_balance` 与 `wallet_input_allowance` 均满足真实链门禁所需条件。

---

## 生成方式（可复核）

### A. 浏览器截图抓取
```bash
node (playwright) 打开以下地址并 full-page screenshot：
- https://sepolia.etherscan.io/tx/0x2ecf681afd170c9c234a5166e595425b6f466db3069882cf21590d87ad822dd4
- https://sepolia.etherscan.io/tx/0x29aa59dff338af035963ce636a9837a7745b4277d3de46a64d984454e439d538
- https://sepolia.etherscan.io/tx/0xf35efaeb6337ee04267192d8c586bd77b6f310b1db9ea7ca15d8e6188c4f796f
```

### B. 链上字段读取
```bash
python(web3) 查询：
- get_transaction
- get_transaction_receipt
- USDC.balanceOf(wallet)
- USDC.allowance(wallet, spender)
```
