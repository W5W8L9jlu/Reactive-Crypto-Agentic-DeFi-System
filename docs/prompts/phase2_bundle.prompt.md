# Prompt Template: Phase2 Bundle

复制下面模板给 Codex，并替换尖括号内容。

```text
Implement Phase2 work for module `<module_id>` only.

Phase2 scope (PRD-aligned):
- Execution Compiler
- Reactive entry trigger
- Validation Engine
- PreRegistrationCheck
- On-chain callback runtime checks
- Reactive stop/tp
- Audit Markdown / Investment Memo export
- Cross-chain interface and multi-chain messaging extension

Goal:
<一句话说明本轮目标，例如：补齐 callback 运行时检查并通过模块测试>

Read these files first, in order:
1. docs/knowledge/01_core/01_system_invariants.md
2. docs/knowledge/01_core/02_domain_models.md
3. docs/contracts/<module_id>.contract.md
4. docs/knowledge/<module-specific-file>.md
5. docs/knowledge/08_delivery/04_phase2_prd_alignment.md
6. docs/contracts/phase2_execution_bundle.contract.md

Only edit:
<module allowed paths from contract>

Hard invariants:
- compile at registration time only
- no recompilation at trigger time
- AI does not output final calldata or signature
- execution trusts RPC truth and compiled plan
- no silent fallback / no swallowed domain exceptions

Do not:
- invent behavior outside knowledge/contracts
- backfill missing specs with implicit defaults
- hide failures with broad try/catch

Definition of done:
<module-specific DoD from contract>

Verification:
1. python scripts/workflow.py check <module_id> --execute --strict
2. <module minimal pytest command if needed>

When spec is missing:
- stop and raise a clear TODO or domain error
- summarize assumptions explicitly
```
