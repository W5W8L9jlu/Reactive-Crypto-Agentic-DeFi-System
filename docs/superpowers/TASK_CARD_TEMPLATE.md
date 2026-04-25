# Task Card Template

> 给 `Product Manager` 和 `Agents Orchestrator` 使用。
> 这张卡会先被整理成 spawn payload，再交给 Codex `spawn_agent`。

## Header

- `模块：`
- `负责人 agent：`
- `状态：Todo / Doing / Blocked / Done`
- `来源：用户目标 / contract / prompt / knowledge`

## 1. 目标

- 本任务要完成什么
- 只写单模块目标
- 必须可验证

## 2. 验收标准

- [ ] 最小验证 1
- [ ] 最小验证 2
- [ ] 最小验证 3

验收标准必须对应模块 `contract` 的 `Minimum Verification`，必要时补充 prompt 约束。

## 3. 非目标

- 本任务不做什么
- 明确禁止的行为
- 跨模块内容

## 4. 风险

- 已知风险
- 未定义行为
- 跨模块接口风险
- 外部依赖风险

## 5. 文件范围

- `Create:`
- `Modify:`
- `Test:`

只列出本模块允许触碰的路径。

## 6. 约束

- 必须保持的 invariants
- 不可生成的内容
- 不可绕过的检查

## 7. 测试计划

- 最小相关测试命令
- 预期结果
- 失败时回退策略

## 8. 交付物

- 产出文件
- 代码/文档/测试
- 需要保留的 TODO
