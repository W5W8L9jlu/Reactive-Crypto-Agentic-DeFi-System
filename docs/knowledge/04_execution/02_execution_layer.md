# Execution Layer

## 目标职责
- 不在校验通过后立即 swap
- 只在 Reactive 条件触发并通过链上运行时检查后执行
- 负责链上调用和回执落库

## 输入
- compiled execution plan
- runtime trigger from reactive system
- on-chain runtime checks passed

## 输出
- `ExecutionRecord`
- tx receipt / logs

## 边界
本模块不做：
- 自由决策
- 重新编译执行计划
- 替代状态机逻辑
