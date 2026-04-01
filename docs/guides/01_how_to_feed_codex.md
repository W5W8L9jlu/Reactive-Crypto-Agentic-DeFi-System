# 如何把模块化知识库喂给 Codex

这套包的目标不是让 Codex 读完整 PRD，而是让它每次只读“当前任务需要的最小上下文”。

## 最推荐的喂法

### 1. 把以下内容放进仓库
- `AGENTS.md` 放在 repo root
- `.codex/config.toml` 放在 repo root
- `docs/knowledge/`
- `docs/contracts/`
- `docs/prompts/`
- `docs/manifests/task_context_manifest.json`

### 2. 每次只做一个模块
一个 Codex session 只做：
- 一个模块
- 一类改动
- 一组相关文件

禁止把多个模块混在同一轮任务里。

### 3. 每次启动任务时，只让 Codex读这些
固定公共上下文：
- `docs/knowledge/01_core/01_system_invariants.md`
- `docs/knowledge/01_core/02_domain_models.md`

模块上下文：
- 对应模块 knowledge
- 对应模块 implementation contract
- 对应模块 prompt template

### 4. Prompt 里显式点名文件
不要说“基于 PRD 实现一下”，要说：
- 读取哪些文件
- 只改哪些目录
- 哪些事情不能做
- 完成标准是什么
- 需要跑什么测试

### 5. 从模块目录启动，会更稳
Codex 会按目录层级读取更近的 `AGENTS.md`。如果你把模块级 `AGENTS.md` 放到相应目录，直接从那个模块目录启动任务，约束会更强。

## 两种喂法

### A. 最稳：AGENTS + 文件点名
适合真正开发。

### B. 最快：打开相关文件 + 粘贴模块 prompt
适合快速原型。

## 一次任务的最小公式

```text
Task
+ Scope
+ Read these files first
+ Only edit these paths
+ Non-goals
+ Done definition
+ Verification commands
```

## 不推荐
- 把整个 PRD 直接贴进 prompt
- 一轮里同时做 compiler + contract + CLI
- 让 Codex 自己猜模块边界
