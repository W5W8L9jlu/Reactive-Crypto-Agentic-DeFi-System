# Phase2 PRD Alignment

## 目的

将 PRD Phase 2 条目映射为仓库可执行任务，作为 `phase_plan` 的补充对齐文档。  
若历史文档与 PRD Phase 2 冲突，以 PRD 为准并在本文件记录调整。

## PRD Phase2 条目映射

| PRD 条目 | 模块落点 | 验收要点 |
| --- | --- | --- |
| Execution Compiler | `execution_compiler` | 注册时编译，触发时不重编译 |
| Reactive 入场触发 | `reactive_runtime`, `execution_layer` | 条件入场可触发，状态可推进 |
| Validation Engine | `validation_engine` | 条件意图校验与拒绝理由可追溯 |
| PreRegistrationCheck | `pre_registration_check` | 基于 RPC 真相执行 allow/reject |
| 链上 Callback 运行时检查 | `execution_layer`, `reactive_runtime` | 非法触发被阻断且错误可诊断 |
| Reactive stop/tp | `reactive_runtime`, `execution_layer` | stop/tp 与注册参数一致 |
| Audit Markdown / Memo 导出 | `export_outputs` | 三轨输出一致且职责分离 |
| 跨链接口/多链消息扩展 | `execution_layer`, `reactive_runtime` | 非空壳，存在最小可验证链路 |

## 依赖顺序

1. `pre_registration_check`
2. `validation_engine`
3. `execution_layer`
4. `execution_compiler`
5. `reactive_runtime`
6. `export_outputs`

## Phase2 Gate（建议）

- 模块级：所有 scope 模块 `workflow check <module> --execute --strict` 通过
- 链路级：`register -> entry trigger -> stop/tp -> export` 最小闭环通过
- 一致性：Machine Truth / Audit Markdown / Memo 字段对齐
- 扩展级：跨链接口/多链消息具备最小可验证路径

## 冲突处理规则

- 文档冲突：以 PRD Phase 2 条目为准
- 合同冲突：以 module contract + invariants 为准
- 实现冲突：优先保证执行真相链路与安全边界，再处理可选扩展
