# AGENTS.md

对该目录的改动，优先遵守：
- `docs/knowledge/04_execution/01_execution_compiler.md`
- `docs/knowledge/04_execution/02_execution_layer.md`
- `docs/contracts/execution_compiler.contract.md`
- `docs/contracts/execution_layer.contract.md`

规则：
- 编译只发生在注册时
- 不在触发时重新编译
- Execution Layer 不做自由决策

## Phase2 Guardrails - Execution

This module owns PreRegistrationCheck, ExecutionCompiler, tx sender, receipt parser, and EventSyncer boundaries.

Must:
- Treat JSON models as Machine Truth.
- Use RPC only for PreRegistrationCheck and runtime event sync.
- Compile register payload at registration time only.
- Preserve `local_intent_id -> onchain_intent_id` mapping.
- Fail fast on disabled features.

Must not:
- Let LLM generate calldata.
- Compile execution payload at trigger time.
- Implement Reactive callback logic inside Python.
- Implement cross-chain execution.
- Implement Uniswap V3.
- Swallow domain exceptions in core business functions.
