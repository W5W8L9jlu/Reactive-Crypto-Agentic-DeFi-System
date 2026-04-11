from __future__ import annotations

import os


REQUIRED_ANY = [
    ("SEPOLIA_RPC_URL", "BASE_SEPOLIA_RPC_URL"),
    ("SEPOLIA_PRIVATE_KEY",),
    ("REACTIVE_INVESTMENT_COMPILER_ADDRESS",),
]


def main() -> int:
    missing_groups: list[tuple[str, ...]] = []
    for group in REQUIRED_ANY:
        if not any(os.environ.get(key) for key in group):
            missing_groups.append(group)
    if missing_groups:
        print("Sepolia smoke env check: FAILED")
        for group in missing_groups:
            print("missing any of:", ", ".join(group))
        return 1
    print("Sepolia smoke env check: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
