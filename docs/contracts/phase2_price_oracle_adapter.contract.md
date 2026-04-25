# Phase2 Price Oracle Adapter Contract

## Module Purpose

Freeze Phase2 price semantics so PreRegistrationCheck, ExecutionCompiler, contract runtime checks, and fixtures use the same direction, scale, and quote behavior.

## Phase2 Scope

Phase2 supports spot-price reads and Uniswap V2-compatible reserve quotes only.

## Out of Scope

- TWAP
- Chainlink aggregation
- Uniswap V3 `sqrtPriceX96`
- multi-hop route selection
- cross-chain oracle reads
- off-chain indexer truth

## Price Direction

`priceE18 = tokenQuote per 1 tokenBase`, scaled by `1e18`.

Example:

```text
tokenBase = WETH
tokenQuote = USDC
priceE18 = 3050e18
```

This means 1 WETH is worth 3050 USDC.

## Public Interface

```solidity
interface IPriceOracleAdapter {
    function getPrice(address tokenBase, address tokenQuote)
        external
        view
        returns (uint256 priceE18);

    function quoteOut(address tokenIn, address tokenOut, uint256 amountIn)
        external
        view
        returns (uint256 amountOut);
}
```

## Required Behavior

- `getPrice()` returns E18-scaled `tokenQuote` per one `tokenBase`.
- `quoteOut()` returns the expected output amount for `tokenIn -> tokenOut`.
- Uniswap V2 reserves are read from the configured pair.
- Token order reversal must be handled explicitly.
- Token decimals must be handled explicitly for USDC 6 decimals and WETH 18 decimals.
- Reserve value of zero must revert or return a clear domain error.
- Unsupported pair must revert or return a clear domain error.

## Failure Modes

- `ReserveUnavailableError`
- `UnsupportedPairError`
- `OraclePriceUnavailableError`
- contract revert for zero reserve or unsupported pair

## Forbidden Behavior

- Do not use The Graph or other indexers as execution truth.
- Do not infer token decimals from string symbols.
- Do not silently return zero price or zero quote.
- Do not use Uniswap V3-specific semantics in Phase2.
- Do not introduce TWAP or Chainlink behavior into the Phase2 main path.

## Tests

Tests must cover:

- WETH/USDC price direction.
- USDC/WETH reverse direction.
- `quoteOut()` with V2 reserve math.
- USDC 6 decimals and WETH 18 decimals.
- zero reserve failure.
- unsupported pair failure.

## Acceptance Criteria

- PreRegistrationCheck, ExecutionCompiler, and contract runtime checks all use this price direction.
- Phase2 fixtures encode prices using this contract.
- W2/W3 smoke evidence can trace price and quote values to this adapter behavior.
