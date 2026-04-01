# PreRegistrationCheck

## 目标职责
- 用 RPC 做注册前状态确认
- 重新确认储备、滑点、余额、allowance、基准 gas、health factor 等
- 计算盈亏平衡点
- 校验 Gas / Expected Profit
- 校验 TTL 是否仍有效
- 决定是否允许注册 Reactive 条件单

## 规则


## 只负责
- 注册时可行性判断

## 不负责
- 运行时最终防守
- 运行时状态机检查

## 依赖
- RPC provider
- Domain Models
- Source of Truth Rules
