# AGENTS.md

## 目标
在本仓库中，优先使用模块化知识库与 implementation contract；禁止默认读取完整 PRD。

## 启动规则
开始任何任务前，先识别目标模块，并按顺序读取：
1. `docs/knowledge/01_core/01_system_invariants.md`
2. `docs/knowledge/01_core/02_domain_models.md`
3. 对应 `docs/contracts/<module>.contract.md`
4. 对应 `docs/knowledge/...` 模块文件
5. 对应 `docs/prompts/<module>.prompt.md`

## 工作边界
- 一个任务只做一个模块，除非用户明确要求跨模块修改。
- 只改 prompt 指定的路径。
- 未在 knowledge/contract 中定义的行为，不得脑补实现。
- 需要跨模块改动时，先输出变更提案与影响面，再等待确认。

## 输出要求
每次完成任务时都给出：
- 修改了哪些文件
- 保持了哪些 invariants
- 跑了哪些验证
- 仍有哪些 TODO / 风险

## 禁止
- 读取完整 PRD 代替模块文档
- 在运行时重新编译 execution plan
- 让 AI 直接生成最终 calldata
- 吞掉核心业务异常

## 补充
- if something you want to find is not defined in current knowledge files,read prd_final_v10.md（"D:\reactive-crypto-agentic-DeFi-system\prd_final_v10.md"）
