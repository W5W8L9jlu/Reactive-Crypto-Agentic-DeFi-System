# Phase 1 Go / No-Go 上线清单

> 用于判断 Phase 1 是否达到“业务可上线”或“严格全链路真实执行也可上线”的门槛。

## 0. 基本信息
- 评估日期：
- 评估人：
- 评估范围：Phase 1
- 结论口径：业务可上线 / 严格全链路真实执行也可上线

## 1. 业务可上线门槛

### 1.1 核心模块最小测试
- [ ] `provider_architecture` 最小测试通过
- [ ] `decision_context_builder` 最小测试通过
- [ ] `strategy_boundary_service` 最小测试通过
- [ ] `validation_engine` 最小测试通过
- [ ] `pre_registration_check` 最小测试通过
- [ ] `approval_flow` 最小测试通过
- [ ] `execution_compiler` 最小测试通过
- [ ] `investment_state_machine_contract` 最小测试通过
- [ ] `execution_layer` 最小测试通过
- [ ] `reactive_runtime` 最小测试通过
- [ ] `shadow_monitor` 最小测试通过
- [ ] `emergency_force_close` 最小测试通过
- [ ] `cli_surface` 最小测试通过
- [ ] `export_outputs` 最小测试通过

### 1.2 用户可见流程
- [ ] CLI 主路径验收通过
- [ ] CLI 受控环境集成验证通过
- [ ] 关键合约/本地链验证通过
- [ ] workflow `audit-manifest --strict` 通过
- [ ] workflow `check --all` 能识别关键模块测试目标

### 1.3 业务可上线判定
- [ ] 核心流程可跑通
- [ ] 用户可见输出可消费
- [ ] 关键门禁已存在
- [ ] 高风险边界已显式记录

结论：
- 业务可上线：`YES / NO`

## 2. 严格全链路真实执行门槛

### 2.1 真实执行链
- [ ] 真实链上执行路径可用
- [ ] 真实回执可读取
- [ ] 真实状态机可推进
- [ ] 真实对账可完成

### 2.2 生产运行条件
- [ ] 部署配置已签收
- [ ] 监控与告警已签收
- [ ] 密钥/权限/回滚方案已签收
- [ ] 故障恢复流程已签收

### 2.3 严格上线判定
- [ ] 真实资金路径闭环
- [ ] 生产级运行态门禁到位
- [ ] 回滚与恢复策略已验证

结论：
- 严格全链路真实执行也可上线：`YES / NO`

## 3. 风险与已知缺口
- 仍需补齐：
- 已确认接受的风险：
- 不进入本次上线门槛的 TODO：

## 4. 证据
- `python scripts/workflow.py audit-manifest --strict`
- `python scripts/workflow.py check --all`
- `python -m pytest backend/validation/test_pre_registration_check.py backend/monitor/test_shadow_monitor.py backend/contracts/core/test_investment_state_machine_contract_emergency_force_close.py backend/cli/test_phase1_end_to_end.py -q`
- `python -m pytest backend/execution/runtime/test_web3_contract_gateway_integration.py -q`

## 5. 最终签字
- 结论：
- 签字人：
- 日期：
