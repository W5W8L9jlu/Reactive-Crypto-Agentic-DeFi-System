# cli_surface 线程交付说明

## 基本信息
- 模块名：`cli_surface`
- Prompt 文件：`docs/prompts/cli_surface.prompt.md`
- Wave：`wave3`
- 负责人：`not verified yet`
- 分支：`w3-reactive-runtime`
- 交付 commit：`9177017`

## 本次交付内容
- 新增 Typer CLI 根入口与六组子命令：
  - `strategy list`
  - `decision run --context-id`
  - `approval show/approve/reject`
  - `execution status`
  - `export bundle`
  - `monitor alerts`
- 新增 CLI surface 错误模型：
  - `CLISurfaceError`
  - `RouteBindingMissingError`
  - `CLISurfaceInputError`
- 新增 monitor alert 视图渲染：
  - `build_alerts_table(...)`
  - `render_alerts_snapshot(...)`
- 新增模块测试：
  - CLI 路由测试
  - 审批显示参数校验测试
  - alert 视图测试

## 修改了哪些文件
- `backend/cli/app.py`
- `backend/cli/errors.py`
- `backend/cli/test_app.py`
- `backend/cli/views/alerts.py`
- `backend/cli/views/test_alerts.py`

## 未交付内容
- 真实 service adapter 绑定（默认仍为显式未绑定错误）
- 跨模块端到端 CLI 运行链路验证
- 线程负责人字段

## 本线程实际执行过的命令
```bash
git diff --name-only HEAD
git log --oneline -n 10
git status -sb
git show --name-only --pretty=format: 9177017
python -m unittest backend.cli.test_app -v
python -m unittest backend.cli.approval.test_approval_flow -v
python -m unittest backend.cli.views.test_alerts -v
```

## 命令结果摘要
- 工作树：干净（`git diff --name-only HEAD` 无输出）
- 模块改动锚点：`9177017`
- 测试：
  - `backend.cli.test_app`：4 passed
  - `backend.cli.approval.test_approval_flow`：5 passed
  - `backend.cli.views.test_alerts`：2 passed

## 对下游影响
- 下游可依赖：
  - 统一 CLI 路由入口与命令组结构
  - 审批展示命令参数约束（`--raw` 需带 machine truth）
  - monitor alert 视图对象与渲染输出
- 下游需补：
  - 将 route handler 绑定到真实业务 service / adapter

