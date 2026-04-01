# 线程交付说明

## 基本信息
- 模块名：`execution_layer`
- Prompt 文件：`docs/prompts/execution_layer.prompt.md`
- Wave：`wave2`
- 负责人：`not verified yet`
- 分支：`master`
- commit：`not verified yet`

## 本次交付做了什么
- 实现了 `execute_runtime_trigger(...)`，只消费已编译执行计划与运行时触发结果
- 增加了 `RuntimeTrigger`、`ChainReceipt`、`ExecutionRecord` 三个运行时模型
- 增加了 execution layer 领域异常：`ExecutionPlanError`、`RuntimeGateError`、`RuntimeTriggerError`、`ReceiptConsistencyError`、`ExecutionAdapterError`
- 通过显式 `ReactiveExecutionPort` 约束链上执行入口，不在模块内做重新编译或自由决策
- 增加了模块级单元测试，覆盖成功回执、失败回执、运行时门禁和 export 兼容性

## 修改了哪些文件
- `backend/execution/runtime/execution_layer.py`
- `backend/execution/runtime/models.py`
- `backend/execution/runtime/errors.py`
- `backend/execution/runtime/__init__.py`
- `backend/execution/runtime/test_execution_layer.py`

## 没做什么
- 没有实现真实链上 executor 适配器
- 没有加入持久化存储；当前“记录回执”表现为返回结构化 `ExecutionRecord`
- 没有加入重新编译逻辑
- 没有加入状态机替代逻辑
- 没有做真实链上或端到端集成验证

## 运行了哪些命令
```bash
git diff --name-only HEAD
git log --oneline -n 10
git branch --show-current
git status --short
python -m unittest -v backend/execution/runtime/test_execution_layer.py
```

## 验收证据
- `git diff --name-only HEAD`：失败，原因是当前仓库没有 `HEAD`
- `git log --oneline -n 10`：失败，原因是当前分支还没有提交
- `git branch --show-current`：输出 `master`
- `python -m unittest -v backend/execution/runtime/test_execution_layer.py`：4 个测试全部通过
- 示例 payload：`RuntimeTrigger`、`ChainReceipt`、最小 `CompiledExecutionPlan` 形状已在 `backend/execution/runtime/test_execution_layer.py` 中给出
- 示例输出：`ExecutionRecord.model_dump(mode="json")` 可被 `backend/export/export_outputs.py` 消费

## 对下游线程的影响
- 新增输入对象：
  - `RuntimeTrigger`
  - `CompiledExecutionPlan` 最小消费形状：`trade_intent_id` + `register_payload.intent_id`
- 新增输出对象：
  - `ExecutionRecord`
  - `ChainReceipt`
- 新增异常：
  - `ExecutionPlanError`
  - `RuntimeGateError`
  - `RuntimeTriggerError`
  - `ReceiptConsistencyError`
  - `ExecutionAdapterError`
- 新增入口：
  - `execute_runtime_trigger(...)`
- 需要下游同步更新的点：
  - executor 实现方必须提供 `execute_reactive_trigger(...)`
  - export / integration 消费方应接受 `ExecutionRecord.model_dump(mode="json")`
