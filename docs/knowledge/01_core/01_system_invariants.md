# System Invariants

这些规则必须在所有模块中保持一致，优先级高于实现细节。

## 核心不变量
- 执行真相唯一来源是结构化 JSON。
- Markdown 审计副本只做摘抄，不做总结生成。
- Investment Memo 可以基于结构化结果和推理过程生成分析报告。
- 执行层只信 RPC，不信第三方索引 API。
- AI 不直接控制资金，不直接生成最终 calldata，不直接签名。
- 所有交易必须先经过策略模板与注册前二次确认。
- 所有执行为条件触发，不做即时市价执行。
- Reactive 负责事件驱动、条件触发和 callback，不负责自由决策。
- 系统必须内建 MEV Protection，Phase 1 不做 MEV Extraction。
- 三轨输出并存：Machine Truth / Audit Markdown / Investment Memo。
- Execution Compiler 工作于注册时，不是触发时。
- 安全检查拆为：链下注册前检查 + 链上运行时硬约束。
- 合约采用 Investment Position State Machine，不采用“链上只发信号、链下再执行”的模式。
- Shadow Monitor 必须独立于 Reactive 运行，并使用备用 RPC 对账。
- 合约必须预留 `emergencyForceClose` 逃生舱。
- 工程实现遵循 Library-First、Lean Defensive Coding、TODO Strategy。

## 关键边界
### AI 层负责
- 投研
- thesis
- 条件意图生成
- Investment Memo

### AI 层不负责
- 最终 calldata
- 签名
- 资金控制
- 链上实时执行决策

### 执行层负责
- 基于已编译执行计划进行注册或执行
- 落库回执
- 运行时检查后的链上动作
