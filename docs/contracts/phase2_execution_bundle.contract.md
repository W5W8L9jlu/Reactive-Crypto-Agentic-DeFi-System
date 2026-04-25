# Implementation Contract: Phase2 Execution Bundle

## Contract ID
`phase2_execution_bundle`

## Purpose
将 PRD Phase 2 目标映射为可执行的跨模块边界合同，约束实现顺序、输入输出和不可越界行为。  
本合同不替代现有模块合同，而是作为 Phase 2 聚合约束层。

## In-Scope Modules
- `execution_compiler`
- `validation_engine`
- `pre_registration_check`
- `execution_layer`
- `reactive_runtime`
- `export_outputs`

## PRD Phase2 Targets (Source of Truth)
- Execution Compiler
- Reactive 入场触发
- Validation Engine
- PreRegistrationCheck
- 链上 Callback 运行时检查
- Reactive stop/tp
- Audit Markdown / Investment Memo 导出
- 跨链接口与多链消息扩展

## Cross-Module Input/Output Contract

### Input Chain
`TradeIntent/StrategyIntent` -> `ValidationResult` -> `ExecutionPlan` -> `Reactive Trigger` -> `ExecutionRecord` -> `Export Outputs`

### Output Guarantees
- 输出必须可落到结构化对象（Pydantic v2）
- 导出层必须保持三轨分离：
  - Machine Truth(JSON)
  - Audit Markdown(摘抄)
  - Investment Memo(分析报告)

## Hard Invariants
- 编译仅在注册时发生
- 触发时禁止重编译
- AI 不生成最终 calldata，不直接签名
- Execution Layer 不做自由决策
- PreRegistrationCheck 仅信 RPC 真相
- Reactive 仅事件驱动，不承担策略决策
- 核心业务函数不吞异常

## Non-goals (Phase2)
- 不重写 Phase1 已稳定模块的既有行为
- 不将 Phase3 模块（approval/shadow_monitor）并入 Phase2 核心门禁
- 不以“容错兜底”掩盖根因问题

## Definition of Done (Phase2 Bundle)
- 六个在 scope 模块都可独立通过最小验证
- `register -> trigger -> stop/tp -> export` 主链路可复现
- callback 运行时检查能阻断非法输入
- 多链/跨链接口具备最小可验证路径
- `workflow check --all --execute --strict` 通过

## Minimum Verification

```powershell
python scripts/workflow.py check execution_compiler --execute --strict
python scripts/workflow.py check validation_engine --execute --strict
python scripts/workflow.py check pre_registration_check --execute --strict
python scripts/workflow.py check execution_layer --execute --strict
python scripts/workflow.py check reactive_runtime --execute --strict
python scripts/workflow.py check export_outputs --execute --strict
python scripts/workflow.py check --all --execute --strict
```

## Handoff Contract
- 跨模块变更必须同步更新对应 module contract / prompt / acceptance evidence
- 未在 knowledge/contract 定义的行为不得脑补；必须 `TODO:` 或显式异常
- 进入 Phase 3 前需先完成 Phase2 Go/No-Go 签收
