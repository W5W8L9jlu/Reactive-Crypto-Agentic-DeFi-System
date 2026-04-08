# 线程交付说明

## 基本信息
- 模块名: `reactive_runtime`
- Prompt 文件: `docs/prompts/reactive_runtime.prompt.md`
- Wave: `wave3`
- 负责人: `not verified yet`
- 分支: `w3-reactive-runtime`
- HEAD commit: `b920945`

## 本次交付做了什么
- 交付了 `backend/reactive/adapters/` 的最小运行时适配层：
  - 强类型模型（intent / trigger / callback result / runtime result）
  - 运行时域错误模型
  - 统一运行入口与状态机端口
  - entry / stop / take 触发与 callback 验证
  - 模块单测

## 模块实现文件（实际存在于当前工作树）
- `backend/reactive/adapters/__init__.py`
- `backend/reactive/adapters/errors.py`
- `backend/reactive/adapters/models.py`
- `backend/reactive/adapters/runtime.py`
- `backend/reactive/adapters/test_reactive_runtime.py`

## 未交付项
- 已提交 commit 锚点：`not verified yet`
- 真实状态机合约联调：`not verified yet`
- execution_layer 联调：`not verified yet`
- callback 回执标准化结构定义：`not verified yet`

## 运行了哪些命令
```bash
git diff --name-only HEAD
git log --oneline -n 10
git status --short --branch
git ls-files --others --exclude-standard -- backend/reactive/adapters
$env:PYTHONPATH='.'; python -m unittest backend.reactive.adapters.test_reactive_runtime -v
```

## 命令结果摘要
- `git diff --name-only HEAD`：空输出
- `git log --oneline -n 10`：最近提交以 `b920945 docs: 回填wave3 cli_surface验收与线程对接文档` 开始，未看到 reactive_runtime 提交锚点
- `git status --short --branch`：`## w3-reactive-runtime...origin/w3-reactive-runtime` + `?? backend/reactive/`
- `python -m unittest ...`：`Ran 5 tests in 0.001s`，`OK`

## 对下游影响
- 下游可按 `backend.reactive.adapters` 暴露接口接入：
  - `run_reactive_runtime_or_raise`
  - `run_reactive_runtime`
  - `InvestmentStateMachinePort`
- 下游不可假设当前模块已形成 commit-level 冻结基线（当前为工作树证据）。
