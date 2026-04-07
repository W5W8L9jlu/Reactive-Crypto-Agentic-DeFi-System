# 线程测试证据

## 测试目标
- 核实 `execution_compiler` 当前分支状态下有哪些文件真正进入了 git 历史
- 核实当前工作树中的 `execution_compiler` 文件是否至少保持语法可编译
- 核实当前仓库是否存在可复现的模块级测试与 compile happy path 证据

## 覆盖的场景
- git 历史 / changed files 核实:
  - 最近提交
  - `HEAD` 下模块 tree
  - 模块目录相对 `HEAD` 的 tracked / untracked 状态
- 语法层验证:
  - `python -m compileall backend/execution/compiler`
- 未覆盖:
  - registration-time compile happy path
  - contract-facing register payload freeze happy path
  - `execution_compiler -> reactive_runtime` 真实 handoff

## 输入
```json
{
  "branch": "w1-gate-fail-fix",
  "head_commit": "c5afba2",
  "module_path": "backend/execution/compiler",
  "historical_module_commit": "1211b50"
}
```

## 输出
```json
{
  "head_tracked_files": [
    "backend/execution/compiler/errors.py",
    "backend/execution/compiler/models.py"
  ],
  "worktree_untracked_files": [
    "backend/execution/compiler/__init__.py",
    "backend/execution/compiler/compiler.py",
    "backend/execution/compiler/test_execution_compiler.py"
  ],
  "compileall": "success",
  "module_happy_path_test": "not verified yet"
}
```

## 命令
```bash
git diff --name-only HEAD
git log --oneline -n 10
git diff --name-only HEAD -- backend/execution/compiler
git ls-files --others --exclude-standard -- backend/execution/compiler
git ls-tree -r --name-only HEAD backend/execution/compiler
git show --stat --summary 1211b50 -- backend/execution/compiler
git show HEAD:backend/execution/compiler/compiler.py
git show HEAD:backend/execution/compiler/test_execution_compiler.py
python -m compileall backend/execution/compiler
```

## 实际结果
- `git log --oneline -n 10`
  - `c5afba2 docs: 更新Wave2验收与交接文档`
  - `1211b50 feat: 实现Wave2执行层与验收文档回填`
- `git ls-tree -r --name-only HEAD backend/execution/compiler`
  - `backend/execution/compiler/errors.py`
  - `backend/execution/compiler/models.py`
- `git diff --name-only HEAD -- backend/execution/compiler`
  - `backend/execution/compiler/errors.py`
  - `backend/execution/compiler/models.py`
- `git ls-files --others --exclude-standard -- backend/execution/compiler`
  - `backend/execution/compiler/__init__.py`
  - `backend/execution/compiler/compiler.py`
  - `backend/execution/compiler/test_execution_compiler.py`
- `git show HEAD:backend/execution/compiler/compiler.py`
  - `fatal: path 'backend/execution/compiler/compiler.py' exists on disk, but not in 'HEAD'`
- `git show HEAD:backend/execution/compiler/test_execution_compiler.py`
  - `fatal: path 'backend/execution/compiler/test_execution_compiler.py' exists on disk, but not in 'HEAD'`
- `python -m compileall backend/execution/compiler`
  - 结果: `success`
  - 输出包含:
    - `Compiling 'backend/execution/compiler\\__init__.py'...`
    - `Compiling 'backend/execution/compiler\\compiler.py'...`
    - `Compiling 'backend/execution/compiler\\errors.py'...`
    - `Compiling 'backend/execution/compiler\\models.py'...`
    - `Compiling 'backend/execution/compiler\\test_execution_compiler.py'...`

## 未验证项
- `python -m unittest backend.execution.compiler.test_execution_compiler -v`: `not verified yet`
  - 原因: 当前工作树中的 `test_execution_compiler.py` 为未跟踪 quarantine 文件，不是 `HEAD` 中的稳定测试资产
- registration-time compile happy path: `not verified yet`
- contract-facing register payload freeze: `not verified yet`
- `execution_compiler -> reactive_runtime` 真实 handoff: `not verified yet`
