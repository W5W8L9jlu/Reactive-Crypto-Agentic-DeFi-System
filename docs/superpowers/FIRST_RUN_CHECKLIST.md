# First Run Checklist

> 这是本项目的首轮执行清单。按模块推进，按门禁放行，不并行扩散。

**目标：** 用一轮可验证的顺序，把核心数据流、决策流、执行流和运行态门禁跑通。
`package` 指模块约束包装层；真实工作使用 task-card / spawn-task 流程生成可交给 Codex `spawn_agent` 的 payload。
`draft` 用于先自动生成 task card 草案，并输出重点摘要 + 完整草案；`approve` 用于人工确认后放行到 spawn payload。
`spawn-decomposition` 用于把已批准的拆分提案整理成可直接派工给 Codex subagent 的角色包；生成的 bundle 会包含 `README.md`，供 Codex 会话按顺序读取。

---

## 1. 入口规则

- 如果一个任务能唯一映射到单一 module_id，并且不需要跨模块边界裁决，直接进入模块级 workflow。
- 如果一个任务跨多个模块、边界不清、依赖顺序未知，先进入 `Project Decomposition` 阶段。
- 如果任务主要是 markdown / README / prompt / playbook / 模板变更，先走文档阶段；只有文档依赖实现结果时，才回到模块级 workflow。

---

## 2. 执行原则

- 一次只做一个 module
- 每个 module 必须先过最小相关测试
- 合约/资金路径必须过安全审计
- 运行态模块必须过 SRE 门
- 不通过测试，不进入下一模块

### 质量门禁

- `Code Reviewer`
  - 触发：代码变更已通过最小测试
  - 输入：diff、测试结果、保持的不变量
  - 输出：审阅结论、问题列表、是否允许进入收口

- `Git Workflow Master`
  - 触发：准备分支收口、提交或 PR
  - 输入：分支状态、提交范围、PR 范围、剩余 review 意见
  - 输出：Git hygiene 结论和收口建议

### 执行补位门禁

- `Senior Developer`
  - 触发：实现涉及跨文件协作、已有实现需要补强，或主执行 agent 明显卡在工程实现细节上
  - 输入：任务卡、当前 diff、相关模块文件、测试反馈
  - 输出：实现建议、补丁方向、需要额外验证的风险点

- `Technical Writer`
  - 触发：实现影响文档、README、prompt、playbook、模板，或需要把提案收口成可审阅文本
  - 输入：实现结果、任务卡、contract 约束、拆分提案/模块报告
  - 输出：最终文档、提案正文、需要同步的文档差异清单

---

## 3. 首轮顺序

### Phase 0: Project Decomposition
- `Product Manager`
- `Workflow Architect`
- `Software Architect`
- `Senior Project Manager`
- `Agents Orchestrator`
- `split` 命令
- `review-split` 命令
- `approve-split` 命令
- `spawn-decomposition` 命令
- `Code Reviewer`
- `Git Workflow Master`
- `Technical Writer`

目标：
- 把项目级目标拆成候选模块、依赖顺序和边界说明
- 产出可供人工确认的模块清单

### Phase 1: Data Foundation
- `provider_architecture`
- `decision_context_builder`

目标：
- 统一 provider 边界
- 产出完整 `DecisionContext`

### Phase 2: Decision Boundary
- `strategy_boundary_service`
- `cryptoagents_adapter`
- `validation_engine`
- `pre_registration_check`

目标：
- 把策略边界、AI 输出和验证收束到强类型对象

### Phase 3: Registration and Execution
- `approval_flow`
- `execution_compiler`
- `investment_state_machine_contract`
- `execution_layer`

目标：
- 把注册、编译、状态机和执行链跑通

### Phase 4: Reactive and Safety
- `reactive_runtime`
- `shadow_monitor`
- `emergency_force_close`

目标：
- 把触发、对账和逃生舱跑通

### Phase 5: Surface and Delivery
- `cli_surface`
- `export_outputs`

目标：
- 把人机交互和三轨输出收尾

### 文档阶段
- `Technical Writer`

目标：
- 把实现后的 `md`、README、prompt、playbook、模板变更收口

控制器执行顺序：
1. 选定项目级目标
2. 做 Project Decomposition
3. `review-split` 查看拆分提案
4. `Workflow Architect`、`Software Architect`、`Senior Project Manager` 进行结构审查
5. `Technical Writer` 汇总成最终拆分提案
6. `approve-split` 放行拆分结果
7. `spawn-decomposition` 生成 role packets
8. 进入单模块 task card 草案
9. 人工 review 草案，不通过就返回修改
10. approve 草案，生成 spawn payload
11. `spawn_agent` 启动 Codex subagent
12. 收集 report
13. 跑最小相关测试
14. `Test Results Analyzer` 判定结果
15. 如果代码变更，先过 `Code Reviewer`
16. 如果改动文档，再过 `Technical Writer`
17. 交付前由 `Git Workflow Master` 收口分支、提交和 PR 流程
18. 分析结果并决定是否进入下一步

| 顺序 | Module | 主执行 agent | 测试执行 | 结果裁决 | 额外门 |
|---|---|---|---|---|---|
| 1 | `provider_architecture` | `Data Engineer` | `API Tester` | `Test Results Analyzer` | `Product Manager` |
| 2 | `decision_context_builder` | `Data Engineer` | `API Tester` | `Test Results Analyzer` | `Product Manager` |
| 3 | `strategy_boundary_service` | `Backend Architect` | `API Tester` | `Test Results Analyzer` | `Product Manager` |
| 4 | `cryptoagents_adapter` | `AI Engineer` | `API Tester` | `Test Results Analyzer` | `Product Manager` |
| 5 | `validation_engine` | `Backend Architect` | `API Tester` | `Test Results Analyzer` | `Product Manager` |
| 6 | `pre_registration_check` | `Backend Architect` | `API Tester` | `Test Results Analyzer` | `Product Manager` |
| 7 | `approval_flow` | `Backend Architect` | `API Tester` | `Test Results Analyzer` | `Product Manager` |
| 8 | `execution_compiler` | `Backend Architect` | `API Tester` | `Test Results Analyzer` | `Product Manager` |
| 9 | `investment_state_machine_contract` | `Solidity Smart Contract Engineer` | `API Tester` | `Test Results Analyzer` | `Blockchain Security Auditor` |
| 10 | `execution_layer` | `Solidity Smart Contract Engineer` | `API Tester` | `Test Results Analyzer` | `Blockchain Security Auditor` |
| 11 | `reactive_runtime` | `Backend Architect` | `API Tester` | `Test Results Analyzer` | `SRE` |
| 12 | `shadow_monitor` | `SRE` | `API Tester` | `Test Results Analyzer` | `SRE` |
| 13 | `emergency_force_close` | `Solidity Smart Contract Engineer` | `API Tester` | `Test Results Analyzer` | `Blockchain Security Auditor` |
| 14 | `cli_surface` | `Backend Architect` | `API Tester` | `Test Results Analyzer` | `Product Manager` |
| 15 | `export_outputs` | `Backend Architect` | `API Tester` | `Test Results Analyzer` | `Product Manager` |

---

## 4. 过关条件

每个 module 只有在以下条件都满足时才能进入下一个：

- `Product Manager` 任务卡已定义
- `API Tester` 已跑最小相关测试
- `Test Results Analyzer` 已判定结果
- 适用时已过 `Blockchain Security Auditor`
- 适用时已过 `SRE`
- 需要文档收口时已过 `Technical Writer`

---

## 5. 回报要求

每个 module 完成后，agent 必须按 [AGENT_REPORT_TEMPLATE.md](./AGENT_REPORT_TEMPLATE.md) 回报。

禁止只报完成。
禁止跳过测试。
禁止把未定义行为写成已实现。
