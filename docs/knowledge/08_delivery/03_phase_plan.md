# Phase Plan

## 部署计划


## Phase 1 / Phase 2


## 开发周期
## 14. 开发周期

### Phase 1（3–5 周）
- CryptoAgents 接入
- DecisionContextBuilder
- TradeIntent / StrategyIntent schema
- CLI 基础
- Strategy Boundary 基础
- RPC + The Graph 最小数据通路

### Phase 2（3–4 周）
- Execution Compiler
- Reactive 入场触发
- Validation Engine
- PreRegistrationCheck
- 链上 Callback 运行时检查
- Reactive stop/tp
- Audit Markdown / Investment Memo 导出

### Phase 3（2–3 周）
- approval flow
- Shadow Monitor
- 数据源优化与日志增强
- Bitquery / Moralis 可选接入
- Aave Protection TODO 模块实现（独立 Sprint）

### 14.1 开发实施路径（Fork + 适配）
建议实施顺序：
1. Fork CryptoAgents 仓库；
2. 保留多 Agent orchestration 与 CLI 主骨架；
3. 替换 `data_fetcher` 为本项目的 `DecisionContextBuilder`；
4. 重写 `Portfolio Manager` Prompt 与 Structured Output；
5. 将输出接入：
   - `StrategyIntent`
   - `TradeIntent`
   - `DecisionMeta`
   - `Investment Memo`
6. 再接入 Reactive 注册与执行链路。

### 14.2 TODO Strategy（新增）
遵循 Happy Path 优先原则：
- 先跑通 `Investment Position State Machine` 主链路；
- 再补旁支风控与外部集成；
- 使用显式 `TODO:` 标记推迟以下模块：
  - Aave Protection 独立实现
  - Telegram / Discord / 钉钉 Webhook
  - Bitquery / Moralis 非主链路接入
  - Postgres / Redis 扩展部署

## 15. 测试用例设计

### 15.1 功能测试
- 生成合法 `StrategyIntent`
- 生成合法 `TradeIntent`
- 模板内通过
- 模板外触发审批
- 越界直接拒绝
- Audit Markdown 与 JSON 一致
- Investment Memo 可生成且不污染执行真相

### 15.2 风控测试
- 超仓位拒绝
- 日内交易次数超限
- 日亏损超限
- 连续亏损熔断
- TTL 过期自动失效
- Aave Protection TODO 模块单独测试，不阻塞主线

### 15.3 链上测试
- Reactive 入场触发成功率
- swap 成功率
- allowance 不足
- balance 不足
- gas 异常
- reserve 突变
- stop/tp 注册成功率
- entryAmountOutMinimum 生效验证
- actualPositionSize 记录验证
- 基于 actualPositionSize + slippageBps 的出场 minOut 计算验证
- emergencyForceClose 生效验证
- maxGasPriceGwei 仅对 PendingEntry 生效验证
- entryValidUntil 仅对 PendingEntry 生效验证
- IntentState 流转验证（PendingEntry -> ActivePosition -> Closed）
- Closed 状态禁止重复执行验证
- Grace Period 后触发 Shadow Monitor 报警验证
- force-close 后迟滞回调 Revert 验证

### 15.4 一致性测试
- JSON 与 Audit Markdown 摘抄一致
- ExecutionRecord 与导出文件一致
- AgentTrace 摘抄字段可追溯
- Investment Memo 与 Audit Markdown 角色分离
- ApprovalBattleCard 与 Machine Truth 数值一致
- `approval show` 默认不直接暴露原始 JSON
- `approval show --raw` 与 Machine Truth 一致

### 15.5 回测与影子模式
- dry-run
- shadow mode
- fork 回放
- 测试结果截图保存，并加时间戳和描述

## 16. 预防过度防御性编程

### 16.1 需要防守的地方
- RPC 真相确认
- schema 校验
- 注册前检查
- 白名单 token/router/pair
- Aave 健康因子阈值（TODO 模块）
- Audit Markdown 摘抄一致性
- 入场 minOut / 出场 slippageBps 合约级限制
- maxGasPriceGwei（仅入场）合约级限制
- TTL（仅入场）合约级限制

### 16.2 不要过度防御的地方
1. **不要每一步都要求人工审批**  
   会让系统失去自动化价值。模板内应允许自动注册与自动触发。

2. **不要把所有第三方 API 全部做三重冗余**  
   成本高、复杂度高，且 Phase 1 不需要。执行层只要 RPC 真相，分析层采用主+辅即可。

3. **不要一开始就建设完整数据平台**  
   当前阶段只做轻量 feature 层，不做全链 ETL。

4. **不要在 Reactive callback 里塞过多业务逻辑**  
   callback 只做触发与最小必要动作，复杂逻辑放回业务层。

5. **不要让 CLI 兼做图形化控制台**  
   当前阶段坚持 CLI-only，避免界面分散工程资源。

6. **不要让 Audit Markdown 承担解释性责任**  
   它是审计副本，不是分析报告。

7. **不要在核心业务函数内部写局部 try-catch 吞异常**  
   `ExecutionCompiler`、`PreRegistrationCheck`、`DecisionContextBuilder` 只负责计算与抛出明确异常（如 `GasTooHighError`、`SlippageExceededError`、`ExpiredIntentError`）。
   由 CLI 主事件循环或全局错误边界统一捕获并渲染为 `ApprovalBattleCard` 或拦截提示。

### 16.3 平衡原则
- 用最少的防守点守住真相链路
- 在自动执行与可审计之间找平衡
- 优先保证“一致性”和“可回放”，而不是“功能堆满”
- 优先跑通 Happy Path，再分 Sprint 补齐旁路模块

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

## 开发实施路径


## TODO Strategy

