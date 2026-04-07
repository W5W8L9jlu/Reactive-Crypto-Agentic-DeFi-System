# Thread Handoff: provider_architecture

- Upstream thread: `provider_architecture`
- Downstream consumer status: `provider-backed fetchers are now evidenced consumers`
- Wave: `W1`
- Branch / HEAD observed: `w1-gate-fail-fix` @ `c5afba2`

## Stable interfaces

- Provider-side request/response contract:
  - `ProviderRequest(operation, params)`
  - `ProviderResponse(provider, operation, payload, metadata)`
- Provider entry points:
  - `RPCProvider.fetch(...)`
  - `GraphProvider.fetch(...)`
  - `EtherscanProvider.fetch(...)`
  - `EtherscanProvider.fetch_or_fallback(...)`
- Downstream consumer seam:
  - `AggregatedMarketFetcher`
  - `AggregatedLiquidityFetcher`
  - `AggregatedOnchainFetcher`
  - `AggregatedRiskFetcher`
  - `AggregatedPositionFetcher`
  - `AggregatedExecutionFetcher`

## Consumer behavior now evidenced

- Provider payloads are parsed into downstream typed models:
  - `MarketTrend`
  - `CapitalFlow`
  - `LiquidityDepth`
  - `OnchainFlow`
  - `RiskState`
  - `PositionState`
  - `ExecutionState`
- Missing required payload fields raise `ProviderDomainError` instead of being silently defaulted.
- Invalid primary payloads can trigger fallback when a fallback provider exists.

## Constraints for downstream work

- Keep provider operations and payload parsing separate from business decisions.
- Keep retry/timeout ownership in the shared provider layer.
- If a new consumer needs additional payload fields, document them before widening provider defaults.

## Verification source

- `$env:PYTHONPATH='.'; pytest backend/data/fetchers/test_aggregated_fetchers.py -q`
  - Result: `4 passed`

## Remaining TODOs

- Provider-backed consumer coverage is now real, but broader multi-module context-builder verification still belongs to the context-builder thread.
