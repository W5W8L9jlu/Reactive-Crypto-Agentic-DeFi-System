# 线程内验收清单

- 模块 / prompt：`export_outputs` / `docs/prompts/export_outputs.prompt.md`
- Wave：`wave_1`
- 线程负责人：`not verified yet`
- 分支：`not verified yet`
- commit：`not verified yet`
- 改动目录：`backend/export`
- 是否只改允许路径：`yes`

## A. 职责边界
- 本模块的目标职责是否完成：`yes`，已实现三轨输出边界的最小闭环。
- 是否引入了不属于本模块的逻辑：`no`，未加入执行、策略判断或审批逻辑。
- 是否修改了共享 schema / 契约：`yes`，新增了模块内输出模型与领域异常。
- 若修改，是否同步通知依赖线程：`not verified yet`

## B. Contract 对齐
- 是否逐条对齐 implementation contract：`yes`
- 未满足项：`docs/knowledge/08_delivery/01_export_outputs.md` 未定义的 memo 模板与空产物语义，按 contract 保留 `TODO` / 明确异常。
- 明确拒绝实现的项（若有）：执行、策略判断、审批逻辑。

## C. Invariants 检查
- 执行 = JSON 真相：`yes`
- 审计 = 摘抄：`yes`
- 报告 = 生成：`yes`
- Audit Markdown 是否改写结论：`no`
- Audit 与 JSON 字段是否 1:1 可追溯：`yes`

## D. 验证证据
- 运行的命令：
  - `git diff --name-only HEAD`，结果：当前工作区不是 git repository，无法读取 HEAD diff
  - `git log --oneline -n 10`，结果：当前工作区没有 commits
  - `python -m unittest backend/export/test_export_outputs.py -v`，结果：通过
  - `python -m pytest backend/export/test_export_outputs.py -q`，结果：失败，当前环境未安装 `pytest`
- 测试结果：`passed`（3 个测试用例）
- 样例输入：`DecisionArtifact` + `ExecutionRecord` 的 Pydantic root payload
- 样例输出：`machine_truth_json`、`audit_markdown`、`investment_memo`
- 截图/日志/回执路径：`not verified yet`

## E. Known gaps
- TODO：`docs/knowledge/08_delivery/01_export_outputs.md` 未定义 Investment Memo 的正式模板。
- TODO：空 `DecisionArtifact` + `ExecutionRecord` 的导出语义未在知识库中定义，当前实现选择抛出 `ExportDomainError`。
- 风险：当前工作区无法通过 git 核对分支与 recent commits。
- 风险：未做更大范围集成验证，仅完成模块级测试。

## F. 可交付结论
- 状态：`PASS_WITH_NOTES`
- 进入线程间对接：`可以`

