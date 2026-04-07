# decision_context_builder 线程交付说明

## 基本信息
- 模块名：`decision_context_builder`
- Wave：`wave2`
- 分支：`w1-gate-fail-fix`
- module commit：`not verified yet`

## 本次交付做了什么
- 当前 workspace 中可交付的模块能力：
  - 在 [builder.py](/D:/reactive-crypto-agentic-DeFi-system/backend/data/context_builder/builder.py) 中提供 `DecisionContextBuilder`
  - 在 [models.py](/D:/reactive-crypto-agentic-DeFi-system/backend/data/context_builder/models.py) 中提供 `DecisionContext` 与相关强类型上下文对象
  - 在 [aggregated_fetchers.py](/D:/reactive-crypto-agentic-DeFi-system/backend/data/fetchers/aggregated_fetchers.py) 中提供 provider-backed 聚合 fetchers
- 当前 diff 中确认落在本模块工作目录的源码改动：
  - [__init__.py](/D:/reactive-crypto-agentic-DeFi-system/backend/data/context_builder/__init__.py)
    - 导出清单按 models / builder / protocols 分组
  - [test_context_builder.py](/D:/reactive-crypto-agentic-DeFi-system/backend/data/context_builder/test_context_builder.py)
    - 增加 `execution_state` 失败路径断言
    - 异步测试改为 `asyncio.run(...)`，避免依赖外部 pytest 插件
  - [__init__.py](/D:/reactive-crypto-agentic-DeFi-system/backend/data/fetchers/__init__.py)
    - 统一为相对导入
  - [aggregated_fetchers.py](/D:/reactive-crypto-agentic-DeFi-system/backend/data/fetchers/aggregated_fetchers.py)
    - `AggregatedExecutionFetcher` 改为 provider 必填
    - `execution_state` 上游失败显式抛 `ProviderDomainError`
  - [test_aggregated_fetchers.py](/D:/reactive-crypto-agentic-DeFi-system/backend/data/fetchers/test_aggregated_fetchers.py)
    - 增加 execution provider 必填测试
    - 增加 execution upstream timeout 测试

## 修改了哪些文件
- 模块源码：
  - `backend/data/context_builder/__init__.py`
  - `backend/data/fetchers/__init__.py`
  - `backend/data/fetchers/aggregated_fetchers.py`
- 模块测试：
  - `backend/data/context_builder/test_context_builder.py`
  - `backend/data/fetchers/test_aggregated_fetchers.py`
- 当前 `git diff --name-only HEAD` 还包含很多与本模块无关的改动；本交付说明只认上面 5 个源码/测试文件。

## 没做什么
- 没有接入真实 provider
- 没有实现链上执行
- 没有实现最终风控裁决
- 没有验证 adapter / compiler / CLI 对 `DecisionContext` 的实际消费
- 没有定义 freshness / staleness 策略

## 运行了哪些命令
```bash
git diff --name-only HEAD
git diff --name-only HEAD -- backend/data/context_builder backend/data/fetchers
git log --oneline -n 10
git branch --show-current
$env:PYTHONPATH='.'; pytest backend/data/fetchers/test_aggregated_fetchers.py backend/data/context_builder/test_context_builder.py -q
```

## 验收证据
- `git branch --show-current` -> `w1-gate-fail-fix`
- `git log --oneline -n 10` -> 当前仅看到 2 条最近提交：
  - `c5afba2 docs: 更新Wave2验收与交接文档`
  - `1211b50 feat: 实现Wave2执行层与验收文档回填`
- 模块测试命令 -> `14 passed, 2 warnings in 2.46s`
  - warning 内容为 `PytestCacheWarning`，与 `.pytest_cache` 写入权限有关

## 对下游线程的影响
- 下游可稳定依赖：
  - `DecisionContextBuilder.build(...) -> DecisionContext`
  - `DecisionContext` 的结构化字段集合
  - builder 层显式错误：
    - `ProviderDataUnavailableError`
    - `DataQualityError`
  - fetcher 层显式错误：
    - `ProviderDomainError`
- 下游需要同步的点：
  - `execution_state` 现在要求显式 provider，不再默认空状态
  - fallback 只在显式配置 fallback provider 的 fetcher 中可用，不应被上层泛化为默认兜底
  - 下游应消费 `DecisionContext`，不要回退到原始 provider payload
