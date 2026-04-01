# Investment Position State Machine

## 核心定位


## 建议接口契约


## 状态流转


## 核心状态
- `PendingEntry`
- `ActivePosition`
- `Closed`

## 关键规则
- 入场成功后记录 `actualPositionSize`
- Closed 状态禁止再次执行
- 入场和出场适用不同约束逻辑
