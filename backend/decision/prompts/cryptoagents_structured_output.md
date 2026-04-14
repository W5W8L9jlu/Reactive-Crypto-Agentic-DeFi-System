Return JSON only.
Do not return markdown.

Output must include:
- pair
- dex
- position_usd
- max_slippage_bps
- stop_loss_bps
- take_profit_bps
- entry_conditions
- ttl_seconds
- projected_daily_trade_count
- investment_thesis
- confidence_score
- agent_trace_steps

Rules:
- conditional intent only
- no market order language
- no calldata
- thesis text must stay separate from execution fields
- pair and dex must match strategy constraints exactly
