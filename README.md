# PRD Codex Kit

这是给 Codex 使用的“最小上下文工程包”，由三层组成：

1. `docs/knowledge/`：模块知识库
2. `docs/contracts/`：implementation contract（模块实现契约）
3. `docs/prompts/`：任务 prompt 模板

还包含：
- `AGENTS.md`：repo 级持久指令
- `.codex/config.toml`：项目级配置样例
- `scripts/build_codex_task_brief.py`：按模块生成任务简报
- `scaffold/`：可复制到真实仓库的目录级 AGENTS 模板

## 推荐使用顺序
1. 把 `AGENTS.md` 放到项目根目录
2. 把 `docs/` 放进仓库
3. 按需要复制 `scaffold/**/AGENTS.md` 到实际代码目录
4. 每次给 Codex 一个模块任务
5. 让它先读：system invariants + domain models + module contract + module prompt

## 目标
让 Codex：
- 不读完整 PRD
- 不跨模块发散
- 不脑补实现边界
- 按 contract 交付
