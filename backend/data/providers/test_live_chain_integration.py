from __future__ import annotations

import asyncio
import os
from decimal import Decimal

import pytest

from backend.data.providers._shared_http_client import ProviderRequest, RetryPolicy
from backend.data.providers.graph_provider import GraphProvider
from backend.data.providers.rpc_provider import RPCProvider


def _run(coro):
    return asyncio.run(coro)


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        pytest.skip(f"{name} is required for live chain integration")
    return value


def _retry_policy() -> RetryPolicy:
    return RetryPolicy(
        max_attempts=2,
        initial_backoff_seconds=0,
        max_backoff_seconds=0,
        backoff_multiplier=1,
    )


def test_live_rpc_provider_roundtrip_reads_real_chain_state():
    rpc_url = _require_env("SEPOLIA_RPC_URL")
    provider = RPCProvider(rpc_url, retry_policy=_retry_policy())

    chain_id = _run(
        provider.fetch(
            ProviderRequest(
                operation="eth_chainId",
                params={"params": []},
            )
        )
    )
    block_number = _run(
        provider.fetch(
            ProviderRequest(
                operation="eth_blockNumber",
                params={"params": []},
            )
        )
    )
    latest_block = _run(
        provider.fetch(
            ProviderRequest(
                operation="eth_getBlockByNumber",
                params={"params": ["latest", False]},
            )
        )
    )
    gas_price = _run(
        provider.fetch(
            ProviderRequest(
                operation="eth_gasPrice",
                params={"params": []},
            )
        )
    )
    zero_balance = _run(
        provider.fetch(
            ProviderRequest(
                operation="eth_getBalance",
                params={"params": ["0x0000000000000000000000000000000000000000", "latest"]},
            )
        )
    )

    chain_id_value = int(chain_id.payload, 16)
    block_number_value = int(block_number.payload, 16)
    gas_price_value = int(gas_price.payload, 16)
    zero_balance_value = int(zero_balance.payload, 16)

    assert chain_id.provider == "rpc"
    assert chain_id_value > 0
    assert block_number.provider == "rpc"
    assert block_number_value > 0
    assert latest_block.payload["number"] == hex(block_number_value)
    assert gas_price_value > 0
    assert zero_balance_value >= 0
    assert chain_id.metadata == {"endpoint": rpc_url}


def test_live_graph_provider_roundtrip_reads_public_subgraph():
    provider = GraphProvider(
        "https://api.studio.thegraph.com/query/48080/sepolia/v2.0.0",
        retry_policy=_retry_policy(),
    )

    try:
        response = _run(
            provider.fetch(
                ProviderRequest(
                    operation="""
                    query LiveAttesters {
                        attesters(first: 1) {
                            attesterId
                            blockNumber
                            epochLength
                            startTimestamp
                            transactionHash
                        }
                    }
                    """.strip(),
                    params={
                        "variables": {},
                        "operation_name": "LiveAttesters",
                    },
                )
            )
        )
    finally:
        _run(provider.close())

    assert response.provider == "the_graph"
    assert response.operation == "LiveAttesters"
    assert isinstance(response.payload, dict)
    assert "attesters" in response.payload
    assert isinstance(response.payload["attesters"], list)
    if response.payload["attesters"]:
        first_row = response.payload["attesters"][0]
        assert first_row["attesterId"]
        assert first_row["blockNumber"]
