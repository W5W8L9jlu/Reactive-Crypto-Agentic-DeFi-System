# 线程交付说明

## 基本信息
- 模块名：`export_outputs`
- Prompt 文件：`docs/prompts/export_outputs.prompt.md`
- Wave：`wave_1`
- 负责人：`not verified yet`
- 分支：`not verified yet`
- commit：`not verified yet`

## 本次交付做了什么
- 实现了 `Machine Truth JSON`、`Audit Markdown Excerpt`、`Investment Memo` 三轨输出。
- 将 `DecisionArtifact` 与 `ExecutionRecord` 包装为 Pydantic root model，输出统一由 `export_outputs(...)` 生成。
- 为空产物与规格缺失场景增加了明确的 `ExportDomainError`。
- 增加了模块级 README，说明三轨边界、摘抄格式与 TODO。

## 修改了哪些文件
- `backend/export/export_outputs.py`
- `backend/export/errors.py`
- `backend/export/__init__.py`
- `backend/export/test_export_outputs.py`
- `backend/export/README.md`

## 没做什么
- 没有加入执行逻辑。
- 没有加入策略判断。
- 没有加入审批逻辑。
- 没有扩展到 `backend/export` 之外的模块。

## 运行了哪些命令
```bash
git diff --name-only HEAD
git log --oneline -n 10
Get-ChildItem -Path D:/reactive-crypto-agentic-DeFi-system/backend/export -File
Get-Content D:/reactive-crypto-agentic-DeFi-system/backend/export/export_outputs.py
Get-Content D:/reactive-crypto-agentic-DeFi-system/backend/export/test_export_outputs.py
Get-Content D:/reactive-crypto-agentic-DeFi-system/backend/export/errors.py
Get-Content D:/reactive-crypto-agentic-DeFi-system/backend/export/__init__.py
python -m unittest backend/export/test_export_outputs.py -v
python -m pytest backend/export/test_export_outputs.py -q
```

## 验收证据
- 测试截图：`not verified yet`
- 日志：`not verified yet`
- 示例 payload：`DecisionArtifact.model_validate({...})`、`ExecutionRecord.model_validate({...})`
- 示例输出：`machine_truth_json` / `audit_markdown` / `investment_memo`

## 对下游线程的影响
- 下游应把 `machine_truth_json` 视为唯一执行真相。
- 下游应把 `audit_markdown` 视为摘抄结果，不应从中重写结论。
- 下游可把 `investment_memo` 当作独立分析报告，不应回写 machine truth。
- 下游若遇到空产物或缺失模板语义，应按 `ExportDomainError` 处理，而不是补默认值。

