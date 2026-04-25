# Phase2 Delivery Playbook

## 目标

按 PRD Phase 2 目标推进开发，并把每个模块都收敛到可验收证据，不以“文档完成”替代“门禁通过”。

## 适用模块

- `pre_registration_check`
- `validation_engine`
- `execution_layer`
- `execution_compiler`
- `reactive_runtime`
- `export_outputs`

## 推荐顺序（按依赖）

1. `pre_registration_check`
2. `validation_engine`
3. `execution_layer`
4. `execution_compiler`
5. `reactive_runtime`
6. `export_outputs`

## 每模块执行循环

1. 读取：`core invariants` + `domain models` + `module contract` + `module knowledge` + `module prompt`
2. 实现：仅改模块允许路径
3. 验证：先跑模块最小测试，再跑 workflow check
4. 收口：补齐 acceptance 证据与风险说明

## 建议命令

```powershell
python scripts/workflow.py package pre_registration_check
python scripts/workflow.py package validation_engine
python scripts/workflow.py package execution_layer
python scripts/workflow.py package execution_compiler
python scripts/workflow.py package reactive_runtime
python scripts/workflow.py package export_outputs
```

模块验证：

```powershell
python scripts/workflow.py check <module_id> --execute --strict
```

Phase2 总门禁：

```powershell
python scripts/workflow.py audit-manifest --strict
python scripts/workflow.py check --all --execute --strict
```

## Phase2 强约束

- 编译仅在注册时进行，触发时禁止重编译
- AI 不生成最终 calldata
- PreRegistrationCheck 仅信 RPC 真相
- Reactive 仅负责事件驱动触发与 callback
- Audit Markdown 仅摘抄，不能覆盖 Machine Truth

## 何时判定 HOLD

- 任一核心模块 `check --strict` 失败
- callback 运行时检查缺失或可被绕过
- stop/tp 与注册参数不一致
- JSON/Audit/Memo 三轨输出字段对不上
- 跨链接口仅有占位，无最小可验证路径
