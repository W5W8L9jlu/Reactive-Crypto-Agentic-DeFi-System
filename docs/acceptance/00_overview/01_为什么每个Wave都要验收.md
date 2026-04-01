# 为什么每个 Wave 都要验收

答案：**需要，而且必须有 gate。**

原因不是流程主义，而是这个项目天然存在这些高耦合边界：
- 执行真相只能来自结构化 JSON，不能被 CLI、Audit、Memo 反向污染
- Execution Compiler 只允许在注册时编译，不允许触发时重新编译
- 链上执行必须落到 Investment Position State Machine，而不是“链下再补一脚”
- Shadow Monitor 必须独立于 Reactive，并使用备用 RPC 对账
- 输出层必须保持 Machine Truth / Audit Markdown / Investment Memo 三轨分离

这些约束一旦在线程里各自“理解”，而没有 wave 级 gate，最常见结果是：
- compile happy path 和 runtime happy path 接不上
- ApprovalBattleCard 的数值来源不可追溯
- CLI 偷偷承担业务逻辑
- Reactive callback 塞入了不该放的业务判断
- export 层和真实执行对象不一致

## 推荐 gate 规则
- Thread gate：该 prompt 对应模块在自己的职责边界内成立
- Wave gate：同一 Wave 的模块组合后成立
- Wave-to-Wave gate：下一 Wave 所依赖的接口、对象、命令和测试证据已经冻结

## 一句话原则
**线程验收看“模块自己站不站得住”，Wave 验收看“模块之间能不能接得上”。**
