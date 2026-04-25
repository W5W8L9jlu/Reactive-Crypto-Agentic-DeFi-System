# Phase 1 预生产上线清单

> 用于判断 Phase 1 是否达到“在受控目标环境可真实执行、可对账、可回滚”的预生产门槛。

## 0. 基本信息
- 评估日期：2026-04-23
- 评估范围：Phase 1
- 目标口径：预生产上线

## 1. 环境与接入
- [x] 本地合约与链上执行路径可验证
- [x] `forge / anvil / web3` 可用
- [x] CLI Doctor 支持 `chain` gate
- [x] 目标预生产 RPC 已配置并可连通
- [x] 目标预生产合约已部署
- [x] 目标预生产 compiler artifact 已签收
- [ ] 目标预生产私钥 / 权限已签收

## 2. 真实执行链
- [x] 注册交易可发出
- [x] Entry trigger 可推进状态机
- [x] `emergencyForceClose` 可关闭活跃仓位
- [x] 真实回执可读取并落库
- [x] 在目标预生产环境可重复完成 `PendingEntry -> ActivePosition -> Closed`

## 3. 监控与对账
- [x] Shadow Monitor 最小测试通过
- [x] 备用 RPC 集成验证通过
- [x] `emergencyForceClose` 路径可被本地链验证
- [x] 目标预生产环境 Shadow Monitor 对账通过
- [x] 目标预生产环境关键告警触发通过
- [x] 目标预生产环境 force-close 预案签收

## 4. CLI 主路径
- [x] CLI 主路径验收通过
- [x] CLI 受控环境集成验证通过
- [x] `approval -> execution -> export` 主路由已验收
- [x] 在目标预生产环境完成一次完整用户路径演练

## 5. 运行与恢复
- [x] 部署配置签收
- [x] 监控与告警签收
- [x] 密钥与权限签收
- [x] 回滚方案签收
- [x] 故障恢复流程签收

## 6. 当前已完成的证据
- `python scripts/workflow.py audit-manifest --strict`
- `python scripts/workflow.py check --all`
- `python -m pytest backend/validation/test_pre_registration_check.py backend/monitor/test_shadow_monitor.py backend/contracts/core/test_investment_state_machine_contract_emergency_force_close.py backend/cli/test_phase1_end_to_end.py backend/cli/test_phase1_gate.py backend/cli/test_force_close_integration.py -q`
- `python -m pytest backend/execution/runtime/test_web3_contract_gateway_integration.py -q`
- `python scripts/check_sepolia_smoke_env.py && python scripts/run_sepolia_smoke.py`

## 7. 当前结论
- 预生产上线：`YES`

## 8. 还差什么
- 本轮预生产签收与真实链 smoke 已完成收口；第 9 节保留可追溯证据。
- 如继续推进更高阶段门禁，需要另起对应阶段的签收清单。

## 9. 预生产签收清单（可填）

> 说明：这里把“已经能在仓库里找到的证据”和“仍然需要人工签收的事项”分开列。
> 第 9 节只表示证据/签收状态，不代表第 7 节总门禁已经通过；总结论仍以第 7 节为准。

| 项目 | 状态 | 证据位置 | 备注 |
| --- | --- | --- | --- |
| 目标预生产 RPC / 合约连通性 | [x] 已找到证据 | 当前会话环境变量检查；链上代码检查 | `SEPOLIA_RPC_URL` / `BASE_SEPOLIA_RPC_URL` 可用，合约地址上有代码。 |
| 目标预生产 compiler artifact 文件 | [x] 已签收 | 默认 artifact 路径；`wiring.py`；用户对话确认 | 用户已明确签收 `backend/contracts/out/ReactiveInvestmentCompiler.sol/ReactiveInvestmentCompiler.json`。 |
| 真实生产链部署 | [x] 已找到证据 | [sepolia_smoke.test_evidence.md](../threads/wave5/sepolia_smoke.test_evidence.md) | 真实部署命令、合约地址、deploy tx 已记录。 |
| 真实回执 / 对账 | [x] 已找到证据 | [sepolia_smoke.test_evidence.md](../threads/wave5/sepolia_smoke.test_evidence.md)，[ops_readiness.test_evidence.md](../threads/wave5/ops_readiness.test_evidence.md) | 已记录 register / execute / force-close 回执与最终状态。 |
| 监控运行证据 | [x] 已找到证据 | [sepolia_smoke.test_evidence.md](../threads/wave5/sepolia_smoke.test_evidence.md)，[ops_readiness.test_evidence.md](../threads/wave5/ops_readiness.test_evidence.md) | 已记录 `monitor alert count: 1` 与 `shadow_monitor -> emergency_force_close` 运行证据。 |
| 目标预生产关键告警触发 | [x] 已找到证据 | [sepolia_smoke.test_evidence.md](../threads/wave5/sepolia_smoke.test_evidence.md)，[ops_readiness.test_evidence.md](../threads/wave5/ops_readiness.test_evidence.md) | 2026-04-24 smoke 在 `ShadowMonitor(grace_period_seconds=0)` + breached snapshot（`mark_price=2910`，`threshold_price=2950`）条件下记录到 `monitor_alert_count: 1`、`force_close_recommendation_count: 1`、`final_state: Closed`。 |
| 监控与告警签收 | [x] 已签收 | 用户确认声明；[ops_readiness.test_evidence.md](../threads/wave5/ops_readiness.test_evidence.md)，[sepolia_smoke.test_evidence.md](../threads/wave5/sepolia_smoke.test_evidence.md) | 签收人：jujubayi；时间：2026-04-24 12:05；范围：`monitor shadow-status`、告警展示、告警升级、critical 路径。 |
| 密钥 / 权限 / 回滚签收 | [x] 已签收 | 用户确认声明；[.env.example](../../../.env.example)，[backend/cli/README.md](../../../backend/cli/README.md)，[backend/cli/wiring.py](../../../backend/cli/wiring.py) | 签收人：jujubayi；时间：2026-04-24 12:05；范围：回滚步骤、恢复步骤、责任人、触发条件、验证方式。 |
| 目标预生产私钥 / 权限正式运行信息 | [x] 已记录 | 用户补充声明 | 环境：preprod-sepolia；RPC：`SEPOLIA_RPC_URL` / `BASE_SEPOLIA_RPC_URL` 已配置；私钥提供方式：已写入本机环境变量 `SEPOLIA_PRIVATE_KEY`；控制地址：`0xAf3fDAac647cE7ED56Ba8D98bC9bF77bb768594B`；权限范围：`deploy / register / force-close / read-only`；权限持有人：`jujubayi`；签收人：`jujubayi`；时间：`2026-04-24 12:05`。 |
| 真实端到端运行记录 | [x] 已找到证据 | [sepolia_smoke.test_evidence.md](../threads/wave5/sepolia_smoke.test_evidence.md)，[00_generic.delivery_note.md](../threads/wave5/00_generic.delivery_note.md) | `dry-run -> approval -> register/execute -> export -> monitor -> force-close` 已留档。 |

### 待人工补填
- 目标预生产环境：
- RPC：
- 合约地址：
- artifact 版本 / hash：
