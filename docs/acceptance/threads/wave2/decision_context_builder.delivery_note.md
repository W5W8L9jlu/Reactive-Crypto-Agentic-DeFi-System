# 线程交付说明

## 基本信息
- 模块名: `decision_context_builder`
- Prompt 文件: `not verified yet`
- Wave: `wave2`
- 负责人: `not verified yet`
- 分支: `master`
- commit: `not verified yet`

## 本次交付做了什么
- 落地 `DecisionContextBuilder.build(...)`，统一聚合并返回完整 `DecisionContext`
- 在 `backend/data/fetchers` 中补齐 provider adapter 层，统一走 `ProviderRequest/ProviderResponse`
- 对 provider 缺字段、坏 payload、超时和 builder 数据质量失败路径抛显式错误
- 补齐模块级测试，覆盖 context 完整性、provider fallback、缺数据/延迟异常

## 修改了哪些文件
- git-tracked changed files: `not verified yet`
  - 原因: `git diff --name-only HEAD` 无法执行，仓库尚无首个提交
- 当前模块交付面已核实的源码文件:
  - `backend/data/context_builder/builder.py`
  - `backend/data/context_builder/models.py`
  - `backend/data/context_builder/__init__.py`
  - `backend/data/context_builder/test_context_builder.py`
  - `backend/data/fetchers/aggregated_fetchers.py`
  - `backend/data/fetchers/__init__.py`
  - `backend/data/fetchers/test_aggregated_fetchers.py`

## 没做什么
- 未做链上执行
- 未做最终风控裁决
- 未做 contract 外 schema 外推
- 未验证 live provider 联调
- 未补其他模块的 acceptance 文档

## 运行了哪些命令
```bash
git diff --name-only HEAD
git log --oneline -n 10
git status --short -b
$env:PYTHONPATH='D:\reactive-crypto-agentic-DeFi-system'; pytest backend/data/context_builder/test_context_builder.py backend/data/fetchers/test_aggregated_fetchers.py -q
```

## 验收证据
- `git diff --name-only HEAD` -> `not verified yet`，原因是仓库无 `HEAD`
- `git log --oneline -n 10` -> `not verified yet`，原因是当前分支无 commits
- `git status --short -b` -> `## No commits yet on master`
- pytest -> `11 passed, 2 warnings in 1.12s`
- 示例 payload / 输出已在测试中以 `ETH/USDC`, `uniswap_v3`, provider mapping payload 形式覆盖

## 对下游线程的影响
- 新增稳定输入对象:
  - `StrategyConstraints`
  - `context_id: str`
- 新增稳定输出对象:
  - `DecisionContext`
- 新增可见异常:
  - `ProviderDataUnavailableError`
  - `DataQualityError`
  - `ProviderDomainError`（fetcher 层）
- 新增入口:
  - `DecisionContextBuilder.build(...)`
  - `AggregatedMarketFetcher.fetch_market_trend(...)`
  - `AggregatedMarketFetcher.fetch_capital_flow(...)`
  - `AggregatedLiquidityFetcher.fetch_liquidity_depth(...)`
  - `AggregatedOnchainFetcher.fetch_onchain_flow(...)`
  - `AggregatedRiskFetcher.fetch_risk_state(...)`
  - `AggregatedPositionFetcher.fetch_position_state(...)`
  - `AggregatedExecutionFetcher.fetch_execution_state(...)`
- 下游需要同步更新的点:
  - 统一按 `DecisionContext` 消费，不直接依赖 provider payload
  - 按显式错误模型处理 provider 缺数据/坏 payload/质量失败
