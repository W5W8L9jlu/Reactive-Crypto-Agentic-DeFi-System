# Reactive Runtime Adapters

最小 Phase 1 适配层，只做三件事：

- 接收已注册的 execution plan，并适配成状态机可注册的 `InvestmentIntent`
- 验证 Reactive callback 是否与当前状态机状态兼容
- 将 entry / stop-loss / take-profit 触发转发到状态机接口

明确不做：

- 自由决策
- 策略评估
- 重新编译执行计划
- 链下兜底计算 `runtime_exit_min_out`

当前显式假设：

- entry callback 只需要 `observed_out`，转发时 `runtime_exit_min_out=0`
- stop-loss / take-profit callback 必须显式携带 `runtime_exit_min_out`
- callback 来源认证机制未在 knowledge/contract 中定义，因此仅做注册绑定与状态兼容校验；更强认证留待后续规范补充
