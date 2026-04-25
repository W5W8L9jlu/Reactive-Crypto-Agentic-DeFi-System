# Phase 2 Go / No-Go 验收清单

> 用于判断 Phase 2 是否达到“可进入多链/跨链执行扩展”的交付门槛。  
> Phase 1 相关验收文档继续保留，本清单仅覆盖 Phase 2 增量目标。

## 0. 基本信息
- 评估日期：
- 评估人：
- 评估范围：Phase 2
- 结论口径：可进入 Phase 3 / 继续 Phase 2 补齐

## 1. Phase 2 范围对齐（PRD）

- [ ] Execution Compiler
- [ ] Reactive 入场触发
- [ ] Validation Engine
- [ ] PreRegistrationCheck
- [ ] 链上 Callback 运行时检查
- [ ] Reactive stop/tp
- [ ] Audit Markdown / Investment Memo 导出
- [ ] 跨链接口与多链消息扩展（按 PRD Phase 2 目标）

## 2. 核心模块门禁

### 2.1 模块最小测试
- [ ] `execution_compiler` 通过
- [ ] `validation_engine` 通过
- [ ] `pre_registration_check` 通过
- [ ] `execution_layer` 通过
- [ ] `reactive_runtime` 通过
- [ ] `export_outputs` 通过

### 2.2 主链路能力
- [ ] `register -> trigger entry -> ActivePosition` 路径可复现
- [ ] stop/tp 可在注册约束内触发
- [ ] Callback 运行时检查可阻断非法触发
- [ ] JSON / Audit Markdown / Memo 三轨输出一致且职责分离

### 2.3 多链与跨链扩展
- [ ] 跨链接口接入路径可验证（非空壳）
- [ ] 多链消息路径有最小可运行证据（mock/fork/testnet 其一）
- [ ] 跨链执行失败路径可回滚/可告警

## 3. 不变量核对

- [ ] 编译只发生在注册时，不在触发时重编译
- [ ] AI 不直接生成最终 calldata，不直接签名
- [ ] Execution Layer 只消费已编译计划，不做自由决策
- [ ] PreRegistrationCheck 只信 RPC 真相
- [ ] Reactive 仅做事件驱动/触发/callback，不做自由策略决策
- [ ] 审计文档仅摘抄，不伪造执行真相

## 4. 证据命令（建议）

```powershell
python scripts/workflow.py audit-manifest --strict
python scripts/workflow.py check execution_compiler --execute --strict
python scripts/workflow.py check validation_engine --execute --strict
python scripts/workflow.py check pre_registration_check --execute --strict
python scripts/workflow.py check execution_layer --execute --strict
python scripts/workflow.py check reactive_runtime --execute --strict
python scripts/workflow.py check export_outputs --execute --strict
python scripts/workflow.py check --all --execute --strict
```

## 5. 判定

- 结果：`GO / HOLD / FAIL`
- 主要阻塞项：
- 风险接受项：
- 进入下一阶段前必须补齐项：

## 6. 最终签字
- 结论：
- 签字人：
- 日期：
