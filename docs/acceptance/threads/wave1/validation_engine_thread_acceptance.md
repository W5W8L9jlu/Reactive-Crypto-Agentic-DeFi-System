# 线程内验收清单

- 模块 / prompt：validation_engine / `docs/prompts/validation_engine.prompt.md`
- Wave：wave_1
- 线程负责人：not verified yet
- 分支：master
- commit：not verified yet; `git log --oneline -n 10` returned "fatal: your current branch 'master' does not have any commits yet"
- 改动目录：`backend/validation/`
- 是否只改允许路径：是

## A. 职责边界
- 本模块的目标职责是否完成：是
- 是否引入了不属于本模块的逻辑：否
- 是否修改了共享 schema / 契约：否
- 若修改，是否同步通知依赖线程：不适用

## B. Contract 对齐
- 是否逐条对齐 implementation contract：是
- 未满足项：`ValidationResult` 仅实现了当前 contract/knowledge 能确认的统一结果结构；更细字段未在文档中定义。
- 明确拒绝实现的项：RPC 查询、calldata 编译、审批展示、链上状态确认

## C. Invariants 检查
- JSON 仍是唯一执行真相：不适用（本模块不生成执行真相）
- Audit 是否只做摘抄：不适用
- Investment Memo 是否未污染执行真相：不适用
- 是否仍然只信 RPC 作为执行真相：不适用
- Execution Compiler 是否只在注册时工作：不适用
- Reactive 是否未承载自由决策：不适用
- Shadow Monitor 是否保持独立：不适用

## D. 验证证据
- 运行的命令：`python -m unittest backend.validation.test_validation_engine`
- 运行的命令：`python -m unittest backend.export.test_export_outputs backend.validation.test_validation_engine`
- 测试结果：两次均通过；前者 5 tests，后者 8 tests
- 样例输入：见 `backend/validation/test_validation_engine.py` 中的 `_valid_payloads()`
- 样例输出：`ValidationResult(is_valid=True, validated_objects=("StrategyTemplate", "StrategyIntent", "TradeIntent", "ExecutionPlan"), issues=())`
- 截图/日志/回执路径：not verified yet

## E. Known gaps
- TODO：模板在 `allowed_pairs` / `allowed_dexes` 为空时的行为仍按 TODO 异常处理
- Blockers：none observed
- 假设：Validation Engine 只负责强类型解析、模型级校验和统一结果输出
- 风险：`ValidationResult` 的更细粒度字段规范未在当前 knowledge 中定义

## F. 可交付结论
- 状态：PASS_WITH_NOTES
- 进入线程间对接：可以
