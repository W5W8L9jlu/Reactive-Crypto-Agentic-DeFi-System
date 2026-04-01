# Risk Register

## 关键风险与缓解
## 17. 关键风险与缓解

### 风险
1. LLM 推理延迟导致状态漂移
2. API 延迟
3. JSON / Markdown 不一致
4. 滑点风险
5. Trigger 执行时的 MEV 夹击
6. Gas 成本侵蚀利润
7. Reactive callback 与业务层脱节
8. 审批等待导致时机失效
9. Reactive 回调迟滞导致仓位裸奔
10. CLI 审批界面信息过载导致判断失误

### 缓解
- TradeIntent 条件化（非即时执行）
- RPC 为执行唯一真相
- Pydantic v2 + Structured Output 强校验
- Audit Markdown 摘抄
- PreRegistrationCheck
- Execution Compiler 前移到注册时
- 合约层强制入场 minOut 与出场动态 minOut
- 合约层对入场阶段强制 gas 上限
- 引入入场阶段 TTL
- Shadow Monitor 监控 Reactive 迟滞
- Reactive 仅做触发与状态流转，不做决策
- ApprovalBattleCard 首屏聚焦关键判断信息

## 18. Reality Check（新增核心章节）

### 18.1 LLM 推理延迟 vs 链上状态漂移
现象：
- CryptoAgents 作为多智能体框架，推理过程可能持续数分钟
- 加密市场数分钟内流动性和价格可能已显著变化

调整：
- 不再让 CryptoAgents 直接做“现在就买”的即时决策
- CryptoAgents 输出未来一段时间内成立的**条件式投资意图**
- 输入数据减少 tick 级噪声，增加小时线 / 日线趋势、资金流趋势、宏观链上行为

### 18.2 TradeIntent 升级
TradeIntent 不再是单纯 Market Order，而必须支持：
- Limit / Conditional Entry
- TTL
- 最大滑点约束

### 18.3 Execution Layer 逻辑后移
以前：
- Validation 通过后立刻执行 swap

现在：
- Validation 通过后先做注册前检查
- Compiler 在注册时直接生成 calldata
- 真正执行只在条件触发时发生
- 触发后链下后端不再插手执行链路

### 18.4 Reactive 层功能扩充
以前：
- 主要负责出场（stop-loss / take-profit）和 Aave 风控

现在：
- 也负责入场
- 引入 Limit Order / Basic Trigger 类适配模式
- 形成统一条件执行层

### 18.5 新挑战：MEV 夹击风险
问题：
- Trigger 触发交易对 MEV 机器人可见
- 若没有严格 `amountOutMinimum`，容易被 sandwich

对策：
- `max_slippage_bps` 必须写入 TradeIntent
- Compiler 在注册时计算 `entryAmountOutMinimum`
- 合约注册参数必须包含 slippage 约束
- 入场 `amountOutMinimum` 必须在合约层生效，而非仅 offchain 检查
- 出场 `amountOutMinimum` 由合约在触发时基于 `actualPositionSize` 与 `slippageBps` 动态计算

### 18.6 Gas 经济模型
问题：
- 单次投资动作可能包含：
  - 条件入场
  - 注册 stop-loss
  - 注册 take-profit
- Gas 成本可能吞噬利润

对策：
- PreRegistrationCheck 必须校验收益 / Gas 比例
- 若预期利润不足覆盖 gas，自动 Abort
- 小仓位、微利策略自动过滤
- Callback 合约仅在入场阶段检查 `tx.gasprice <= params.maxGasPriceGwei`，出场阶段豁免该限制

### 18.7 Reactive 依赖与异步执行风险
问题：
- Reactive callback 可能延迟或失败
- stop-loss 可能击穿后才被执行

对策：
- 引入 Shadow Monitor
- Shadow Monitor 使用备用 RPC 做状态对账，而不是依赖 Reactive 自身状态
- 若价格已击穿阈值但 callback 未发生，CLI 发出高危告警
- CLI 提供强制手动平仓能力
- 通过 Grace Period 避免与正常回调并发冲突

### 18.8 人工审批打断体验
问题：
- 模板外意图如果长时间等待审批，交易条件可能已失效

对策：
- 所有待审批 `TradeIntent` 必须带 TTL
- 超时自动失效
- 禁止审批过期意图

### 18.9 纯链上闭环的时空重定位
结论：
- Execution Compiler 的工作时机必须从“触发时”前移到“注册时”
- 安全检查必须拆成：
  - 链下注册前检查（PreRegistrationCheck）
  - 链上运行时硬检查（On-chain Runtime Check）
- 智能合约本体不再是简单 Trigger，而是 Investment Position State Machine
- 编译器在注册时一次性把入场绝对约束（entry minOut / Gas 上限 / TTL）与出场相对约束（stop/take slippageBps）打包上链

这样既保留 Reactive 的毫秒级优势，又保持安全边界。

### 18.10 投资仓位状态机的工程收益
- 把入场与出场统一到同一个链上 Intent 中，避免在 Basic Trigger 之上做过度二次开发
- 把仓位生命周期显式建模为 `PendingEntry -> ActivePosition -> Closed`
- 让后端只负责“下达附带军规的死命令”，前线由 Reactive 在链上无情执行
- 让 InvestmentIntent 成为长期投资系统的核心原语，更贴合专业链上基金式的仓位管理

### 18.11 Shadow Monitor 的非对称监听机制
- Shadow Monitor 是独立于主业务进程的轻量级守护进程或定时任务
- 它直接使用备用 RPC（例如主用 Alchemy，监控使用 Infura / QuickNode）做状态对账
- 它只处理状态为 `ActivePosition` 的意图
- 它比较两件事：
  1. 当前价格是否已经击穿止损线或突破止盈线；
  2. 合约状态是否仍未从 `ActivePosition` 转移。

#### Grace Period
- 当首次发现“该死却没死”的状态时，不立即报警
- 默认给予 3 个区块或 1 分钟缓冲
- Grace Period 结束后状态仍未变化，则升级为最高级别警报

### 18.12 Emergency Force Close（逃生舱）
在极端情况下，系统必须允许管理员绕过 Reactive 正常回调路径，直接发起紧急平仓。

链上接口要求：
```solidity
function emergencyForceClose(uint256 intentId, uint256 maxSlippageBps) external onlyOwner;
```

执行要求：
- 仅在 `IntentState == ActivePosition` 时允许调用
- 调用前先把状态强制写为 `Closed`
- 紧急卖出允许较宽滑点，以“逃命优先”为原则
- 任何后续迟滞到达的正常回调，都必须因为状态已为 `Closed` 而直接 Revert

工程收益：
- 避免并发竞争与重复平仓
- 为 ICU 级异常提供最后的手动逃生能力

## 19. MEV 策略边界

### Phase 1
- ✅ MEV Protection
- ❌ MEV Extraction

说明：
- 当前系统首先需要的是自我保护，而不是把主动做 MEV 搜索作为主业务线
- 主动 MEV 搜索属于另一类高复杂度系统，不进入 Phase 1

## 20. 最终结论

这是一个：

> **以 CryptoAgents 为投研内核、以 Strategy Boundary 为规则边界、以 Reactive 为纯链上条件执行引擎、以 Execution Compiler 为注册时执行桥梁、以 RPC 为执行真相的 CLI 单链 DeFi 链上投资系统。**

## Reality Check
## 18. Reality Check（新增核心章节）

### 18.1 LLM 推理延迟 vs 链上状态漂移
现象：
- CryptoAgents 作为多智能体框架，推理过程可能持续数分钟
- 加密市场数分钟内流动性和价格可能已显著变化

调整：
- 不再让 CryptoAgents 直接做“现在就买”的即时决策
- CryptoAgents 输出未来一段时间内成立的**条件式投资意图**
- 输入数据减少 tick 级噪声，增加小时线 / 日线趋势、资金流趋势、宏观链上行为

### 18.2 TradeIntent 升级
TradeIntent 不再是单纯 Market Order，而必须支持：
- Limit / Conditional Entry
- TTL
- 最大滑点约束

### 18.3 Execution Layer 逻辑后移
以前：
- Validation 通过后立刻执行 swap

现在：
- Validation 通过后先做注册前检查
- Compiler 在注册时直接生成 calldata
- 真正执行只在条件触发时发生
- 触发后链下后端不再插手执行链路

### 18.4 Reactive 层功能扩充
以前：
- 主要负责出场（stop-loss / take-profit）和 Aave 风控

现在：
- 也负责入场
- 引入 Limit Order / Basic Trigger 类适配模式
- 形成统一条件执行层

### 18.5 新挑战：MEV 夹击风险
问题：
- Trigger 触发交易对 MEV 机器人可见
- 若没有严格 `amountOutMinimum`，容易被 sandwich

对策：
- `max_slippage_bps` 必须写入 TradeIntent
- Compiler 在注册时计算 `entryAmountOutMinimum`
- 合约注册参数必须包含 slippage 约束
- 入场 `amountOutMinimum` 必须在合约层生效，而非仅 offchain 检查
- 出场 `amountOutMinimum` 由合约在触发时基于 `actualPositionSize` 与 `slippageBps` 动态计算

### 18.6 Gas 经济模型
问题：
- 单次投资动作可能包含：
  - 条件入场
  - 注册 stop-loss
  - 注册 take-profit
- Gas 成本可能吞噬利润

对策：
- PreRegistrationCheck 必须校验收益 / Gas 比例
- 若预期利润不足覆盖 gas，自动 Abort
- 小仓位、微利策略自动过滤
- Callback 合约仅在入场阶段检查 `tx.gasprice <= params.maxGasPriceGwei`，出场阶段豁免该限制

### 18.7 Reactive 依赖与异步执行风险
问题：
- Reactive callback 可能延迟或失败
- stop-loss 可能击穿后才被执行

对策：
- 引入 Shadow Monitor
- Shadow Monitor 使用备用 RPC 做状态对账，而不是依赖 Reactive 自身状态
- 若价格已击穿阈值但 callback 未发生，CLI 发出高危告警
- CLI 提供强制手动平仓能力
- 通过 Grace Period 避免与正常回调并发冲突

### 18.8 人工审批打断体验
问题：
- 模板外意图如果长时间等待审批，交易条件可能已失效

对策：
- 所有待审批 `TradeIntent` 必须带 TTL
- 超时自动失效
- 禁止审批过期意图

### 18.9 纯链上闭环的时空重定位
结论：
- Execution Compiler 的工作时机必须从“触发时”前移到“注册时”
- 安全检查必须拆成：
  - 链下注册前检查（PreRegistrationCheck）
  - 链上运行时硬检查（On-chain Runtime Check）
- 智能合约本体不再是简单 Trigger，而是 Investment Position State Machine
- 编译器在注册时一次性把入场绝对约束（entry minOut / Gas 上限 / TTL）与出场相对约束（stop/take slippageBps）打包上链

这样既保留 Reactive 的毫秒级优势，又保持安全边界。

### 18.10 投资仓位状态机的工程收益
- 把入场与出场统一到同一个链上 Intent 中，避免在 Basic Trigger 之上做过度二次开发
- 把仓位生命周期显式建模为 `PendingEntry -> ActivePosition -> Closed`
- 让后端只负责“下达附带军规的死命令”，前线由 Reactive 在链上无情执行
- 让 InvestmentIntent 成为长期投资系统的核心原语，更贴合专业链上基金式的仓位管理

### 18.11 Shadow Monitor 的非对称监听机制
- Shadow Monitor 是独立于主业务进程的轻量级守护进程或定时任务
- 它直接使用备用 RPC（例如主用 Alchemy，监控使用 Infura / QuickNode）做状态对账
- 它只处理状态为 `ActivePosition` 的意图
- 它比较两件事：
  1. 当前价格是否已经击穿止损线或突破止盈线；
  2. 合约状态是否仍未从 `ActivePosition` 转移。

#### Grace Period
- 当首次发现“该死却没死”的状态时，不立即报警
- 默认给予 3 个区块或 1 分钟缓冲
- Grace Period 结束后状态仍未变化，则升级为最高级别警报

### 18.12 Emergency Force Close（逃生舱）
在极端情况下，系统必须允许管理员绕过 Reactive 正常回调路径，直接发起紧急平仓。

链上接口要求：
```solidity
function emergencyForceClose(uint256 intentId, uint256 maxSlippageBps) external onlyOwner;
```

执行要求：
- 仅在 `IntentState == ActivePosition` 时允许调用
- 调用前先把状态强制写为 `Closed`
- 紧急卖出允许较宽滑点，以“逃命优先”为原则
- 任何后续迟滞到达的正常回调，都必须因为状态已为 `Closed` 而直接 Revert

工程收益：
- 避免并发竞争与重复平仓
- 为 ICU 级异常提供最后的手动逃生能力

## 19. MEV 策略边界

### Phase 1
- ✅ MEV Protection
- ❌ MEV Extraction

说明：
- 当前系统首先需要的是自我保护，而不是把主动做 MEV 搜索作为主业务线
- 主动 MEV 搜索属于另一类高复杂度系统，不进入 Phase 1

## 20. 最终结论

这是一个：

> **以 CryptoAgents 为投研内核、以 Strategy Boundary 为规则边界、以 Reactive 为纯链上条件执行引擎、以 Execution Compiler 为注册时执行桥梁、以 RPC 为执行真相的 CLI 单链 DeFi 链上投资系统。**

## MEV 策略边界
## 19. MEV 策略边界

### Phase 1
- ✅ MEV Protection
- ❌ MEV Extraction

说明：
- 当前系统首先需要的是自我保护，而不是把主动做 MEV 搜索作为主业务线
- 主动 MEV 搜索属于另一类高复杂度系统，不进入 Phase 1

## 20. 最终结论

这是一个：

> **以 CryptoAgents 为投研内核、以 Strategy Boundary 为规则边界、以 Reactive 为纯链上条件执行引擎、以 Execution Compiler 为注册时执行桥梁、以 RPC 为执行真相的 CLI 单链 DeFi 链上投资系统。**

## 最终定位
## 20. 最终结论

这是一个：

> **以 CryptoAgents 为投研内核、以 Strategy Boundary 为规则边界、以 Reactive 为纯链上条件执行引擎、以 Execution Compiler 为注册时执行桥梁、以 RPC 为执行真相的 CLI 单链 DeFi 链上投资系统。**
