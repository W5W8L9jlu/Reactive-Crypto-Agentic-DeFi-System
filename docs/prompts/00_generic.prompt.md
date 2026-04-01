# Generic Prompt Template

```text
Implement ONLY one module.

Module:
<module_id>

Task:
<what to do in this round>

Read first:
1. docs/knowledge/01_core/01_system_invariants.md
2. docs/knowledge/01_core/02_domain_models.md
3. docs/contracts/<module_id>.contract.md
4. docs/prompts/<module_id>.prompt.md
5. the module knowledge file listed in the contract

Only edit:
- <paths>

Do not:
- cross module boundaries
- invent behavior absent from spec
- read the full PRD unless explicitly requested

Return:
- changed files
- invariants preserved
- tests run
- assumptions / TODOs
```
