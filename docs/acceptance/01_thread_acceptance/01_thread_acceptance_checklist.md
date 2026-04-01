# 线程内验收清单（模板）

- 模块 / prompt：
- Wave：
- 线程负责人：
- 分支：
- commit：
- 改动目录：
- 是否只改允许路径：是 / 否

## A. 职责边界
- 本模块的目标职责是否完成：
- 是否引入了不属于本模块的逻辑：
- 是否修改了共享 schema / 契约：是 / 否
- 若修改，是否同步通知依赖线程：是 / 否

## B. Contract 对齐
- 是否逐条对齐 implementation contract：是 / 否
- 未满足项：
- 明确拒绝实现的项（若有）：

## C. Invariants 检查
- JSON 仍是唯一执行真相：是 / 否 / 不适用
- Audit 是否只做摘抄：是 / 否 / 不适用
- Investment Memo 是否未污染执行真相：是 / 否 / 不适用
- 是否仍然只信 RPC 作为执行真相：是 / 否 / 不适用
- Execution Compiler 是否只在注册时工作：是 / 否 / 不适用
- Reactive 是否未承载自由决策：是 / 否 / 不适用
- Shadow Monitor 是否保持独立：是 / 否 / 不适用

## D. 验证证据
- 运行的命令：
- 测试结果：
- 样例输入：
- 样例输出：
- 截图/日志/回执路径：

## E. Known gaps
- TODO：
- Blockers：
- 假设：
- 风险：

## F. 可交付结论
- 状态：PASS / PASS_WITH_NOTES / FAIL
- 进入线程间对接：可以 / 不可以
