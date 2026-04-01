# DecisionContextBuilder

## 目标职责
- 从多数据源取数
- 轻量特征工程
- 统一上下文结构
- 屏蔽 provider 差异

## 输入视角改造


## 数据接入改造策略


## 依赖模块
- Provider Architecture
- Source of Truth Rules
- Domain Models

## 并行开发接口
输入：
- strategy constraints
- provider snapshots

输出：
- `DecisionContext`

## 原则
- 减少 tick 级噪声
- 强化趋势 / 资金流 / 风险环境 / 仓位态输入
- 执行层真相不来自这里，只作决策与注册前辅助
