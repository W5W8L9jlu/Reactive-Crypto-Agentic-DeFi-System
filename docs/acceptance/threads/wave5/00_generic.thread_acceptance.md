# 线程验收清单
- 模块 / prompt: `00_generic` / `not verified yet`
- Wave: `wave5`
- 线程负责人: `not verified yet`
- 分支: `codex/wave5`
- HEAD commit: `8e56fbd`
- 改动目录: `backend/cli`, `backend/contracts`, `backend/decision`, `backend/execution/runtime`, `backend/export`, `backend/validation`
- 是否只改允许路径: `not verified yet`（本轮是跨模块 fix-plan）

## A. Scope
- 已完成（基于当前工作树）：
  - `cli_surface`：Typer 参数注解兼容修复（`Optional[str]`），命令面扩展（`strategy create/show/edit`、`decision dry-run`、`execution force-close/fork-replay`、`export json/markdown/memo`、`monitor shadow-status`）。
  - `shadow_monitor -> cli`：critical 告警新增 force-close 横幅文案（含 `agent-cli execution force-close <intent-id>`）。
  - `execution_layer/runtime`：新增 `recommendation -> emergencyForceClose` 参数映射与 gateway 调用路径。
  - 合约接口一致性：`IReactiveInvestmentCompiler.sol` 已声明 emergency 相关接口与错误；`ReactiveInvestmentCompiler.t.sol` 补 emergency 专项断言。
- 非目标保持未实现：
  - `shadow_monitor -> emergency` 真链路 E2E（`web3/anvil` 依赖）仍未在本环境验证。

## B. Contract 对齐
- `docs/contracts/cryptoagents_adapter.contract.md`：输出结构化对象、thesis 与执行字段分离，`backend/decision/schemas/test_cryptoagents_adapter.py` 通过。
- `docs/contracts/execution_layer.contract.md`：runtime 仅负责链上调用与回执记录，`backend/execution/runtime/test_execution_layer.py` 通过。
- `IReactiveInvestmentCompiler` 与合约实现 emergency 方法签名：当前工作树对齐，`forge` 用例通过。

## C. Invariants 检查
- JSON 是唯一执行真相：`verified`（`backend/export/export_outputs.py` 与 `backend/export/test_export_outputs.py`）
- Audit 只做摘抄：`verified`（`# Audit Markdown Excerpt` 由 JSON leaf 摘抄生成）
- Memo 与执行真相隔离：`verified`（Memo 明确声明“执行以 Machine Truth JSON 为唯一来源”）
- Execution Compiler 只在注册时工作：`partially verified`（编译器/验证测试通过；端到端触发时不重编译路径 not verified yet）
- Shadow Monitor 独立运行：`partially verified`（模块级与 CLI 告警展示通过；跨线程真链路 not verified yet）

## D. 验证证据（本轮实际命令）
- `git diff --name-only HEAD`：当前工作树包含 CLI、合约、compiler、export、validation 等改动。
- `git log --oneline -n 10`：最新提交为 `8e56fbd docs: 冻结W4到W5波次交接基线与依赖边界`。
- `pytest backend/cli/test_app.py -q`（带 `PYTHONPATH=.`）：`5 passed`
- `pytest backend/cli/approval/test_approval_flow.py backend/cli/views/test_alerts.py -q`（带 `PYTHONPATH=.`）：`7 passed`
- `pytest backend/decision/schemas/test_cryptoagents_adapter.py -q`（带 `PYTHONPATH=.`）：`1 passed`
- `pytest backend/execution/runtime/test_execution_layer.py -q`（带 `PYTHONPATH=.`）：`1 passed`
- `pytest backend/execution/runtime/test_contract_gateway.py -q`（带 `PYTHONPATH=.`）：`3 passed`
- `pytest backend/execution/runtime/test_web3_contract_gateway_integration.py -q`（带 `PYTHONPATH=.`）：`3 skipped`
- `pytest backend/decision/orchestrator/test_main_chain_service.py -q`（带 `PYTHONPATH=.`）：`2 passed`
- `pytest backend/decision/adapters/test_cryptoagents_runner.py -q`（带 `PYTHONPATH=.`）：`2 passed`
- `pytest ...14个模块回归集合... -q`（带 `PYTHONPATH=.`）：`58 passed`
- `forge test --root . --contracts backend/contracts/test --match-path backend/contracts/test/ReactiveInvestmentCompiler.t.sol -vv`：`12 passed`

## E. Known gaps
- `backend/decision/` 与 `backend/execution/runtime/` 仍是未跟踪目录（`git status` 显示 `??`），仓库基线未冻结：`not verified yet`
- `web3/anvil` 依赖下的集成闭环测试为 `skipped`：`not verified yet`
- 工作区仍包含大量生成物改动（`out/`, `cache/`, `backend/contracts/out/`），发布快照不干净：`not verified yet`

## F. 结论
- 线程状态：`PASS_WITH_NOTES`
- 进入线程间对接：`可以（需携带未验证项）`
- 作为 Phase 1 发布快照直接交付：`不可以`
