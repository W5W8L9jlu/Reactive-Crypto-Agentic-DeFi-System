# Wave 内验收 Gate（模板）

- Wave：
- Gate owner：
- 日期：
- 参与线程：
- 相关分支 / commit：

## A. 完整性
- 本 Wave 所有 prompt 是否都有线程交付：是 / 否
- 每个线程是否都提交了 thread acceptance：是 / 否
- 每个线程是否都提交了 thread handoff：是 / 否

## B. 依赖对齐
- 上下游接口是否冻结：是 / 否
- 示例 payload 是否一致：是 / 否
- 异常模型是否一致：是 / 否
- 命名与目录是否一致：是 / 否

## C. Wave 级最小集成
- 本 Wave 最小 happy path 是否可跑通：是 / 否
- 是否存在“单线程通过但组合失败”：是 / 否
- 是否存在共享 schema 冲突：是 / 否

## D. 不变量复核
- 执行真相仍为 JSON：是 / 否
- 审计/报告边界仍清晰：是 / 否
- 执行编译仍前移到注册时：是 / 否
- Reactive 仍只负责条件触发与状态流转：是 / 否
- Shadow Monitor 仍保持独立：是 / 否 / 不适用

## E. Gate 结论
- 结论：PASS / PASS_WITH_NOTES / FAIL
- 允许进入下一 Wave：是 / 否
- 必修问题：
- 可带入下一 Wave 的已知问题：
