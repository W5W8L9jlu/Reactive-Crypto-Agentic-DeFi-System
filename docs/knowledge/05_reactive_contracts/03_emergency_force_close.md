# Emergency Force Close

## 功能目标


## CLI 告警与操作流


## 合约级规则
- 仅 owner / authorized relayer 调用
- 仅 `ActivePosition` 时允许调用
- 调用前先将状态写为 `Closed`
- 使用更宽滑点，以逃命优先
- 后续迟滞正常回调必须 Revert
