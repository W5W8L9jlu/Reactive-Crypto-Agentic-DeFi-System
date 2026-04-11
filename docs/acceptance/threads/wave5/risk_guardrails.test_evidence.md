# 风险护栏线程测试证据（2026-04-10）

## 范围
- 日亏损上限（`projected_daily_loss_pct_nav`）边界规则
- 连续亏损熔断（`projected_consecutive_loss_count`）边界规则
- `shadow_monitor` recommendation 驱动 `emergency_force_close` 的关键链路用例

## 代码落点
- `backend/strategy/models.py`
- `backend/strategy/strategy_boundary_service.py`
- `backend/validation/test_strategy_risk_boundaries.py`
- `backend/cli/wiring.py`
- `backend/cli/test_wiring.py`
- `backend/cli/entrypoint.py`
- `pyproject.toml`

## 命令与结果
```bash
python -m unittest backend.validation.test_strategy_risk_boundaries -v
# 结果: Ran 3 tests ... OK

python -m unittest backend.cli.test_wiring -v
# 结果: Ran 8 tests ... OK

python -m unittest discover -s backend -p 'test*.py' -v
# 结果: Ran 18 tests ... OK

python -m unittest backend.execution.runtime.test_web3_contract_gateway_integration.Web3ContractGatewayIntegrationTestCase.test_shadow_monitor_recommendation_drives_emergency_force_close -v
# 结果: Ran 1 test ... OK

C:\Python314\python.exe scripts/run_phase1_regression.py --with-chain
# 结果: 统一回归命令通过（含 unittest discover + runtime pytest 集成 + CLI force-close 集成）
```

## 通过项
- `projected_daily_loss_pct_nav`：
  - auto 边界内 -> `auto_register`
  - 超过 auto 且不超过 hard -> `manual_approval`
- `projected_consecutive_loss_count`：
  - 超过 hard -> `reject`
- `test_shadow_monitor_recommendation_drives_emergency_force_close`：通过（`ok`）

## 说明
- 本轮“可复现”证据定义沿用：CLI 路由可调用 + 自动化测试通过。
- 本轮不包含 Sepolia 实链 smoke（`decision dry-run -> approval -> register/execute -> export -> monitor -> force-close`）。
