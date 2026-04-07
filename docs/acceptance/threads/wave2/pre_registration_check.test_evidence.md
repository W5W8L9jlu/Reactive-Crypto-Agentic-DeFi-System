# pre_registration_check 线程测试证据

## 测试目标
- 确认 `pre_registration_check` 实现文件至少满足语法可编译
- 确认仓库内是否存在专门测试文件
- 尝试做最小运行时 smoke，检查模块是否能通过当前包路径被导入

## 覆盖的场景
- 语法检查：
  - `backend/validation/pre_registration_check.py` 可被 `py_compile`
- 仓库结构检查：
  - 是否存在 `pre_registration_check` 专门测试文件
- 运行时 smoke：
  - 通过 `backend.validation.pre_registration_check` 包路径导入模块

## 命令
```bash
Get-ChildItem -Recurse -File backend | Where-Object { $_.Name -match 'pre_registration_check|pre-registration-check' } | Select-Object FullName
python -m py_compile backend/validation/pre_registration_check.py
@'
from backend.validation.pre_registration_check import run_pre_registration_check
print(run_pre_registration_check)
'@ | python -
```

## 输入
- 文件搜索输入：`backend/**`
- 语法检查输入：`backend/validation/pre_registration_check.py`
- 运行时 smoke 输入：`backend.validation.pre_registration_check`

## 输出
- 文件搜索输出：
  - `backend/validation/pre_registration_check.py`
  - `backend/validation/__pycache__/pre_registration_check.cpython-314.pyc`
- 语法检查输出：无输出，exit code 0
- 运行时 smoke 输出：未进入场景断言；在导入阶段失败

## 实际结果
- 通过：
  - `python -m py_compile backend/validation/pre_registration_check.py`
- 失败：
  - 内联 Python smoke 失败，报错：
    - `ImportError: cannot import name 'RegisterPayload' from 'backend.execution.compiler.models'`
  - 失败根因已定位到当前工作树中的包级导入链：
    - `backend.validation.__init__`
    - `backend.validation.models`
    - `backend.execution.compiler.models`
- 未覆盖：
  - dedicated unit tests：`not verified yet`
  - precheck happy path runtime pass：`not verified yet`
  - gas / TTL / allowance / balance / slippage / profitability 的自动化断言：`not verified yet`

## 备注
- 当前 repo 中未发现 `pre_registration_check` 专门测试文件。
- 当前证据只能证明：
  - 单文件语法成立
  - 当前工作树的包级运行时导入被上游模型文件状态阻塞
