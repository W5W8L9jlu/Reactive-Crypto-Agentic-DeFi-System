# 并行开发映射

## 依赖图（简化）

```text
System Invariants
  ├── Domain Models
  │    ├── Decision
  │    ├── Strategy/Validation
  │    ├── Execution Compiler
  │    ├── Reactive Contracts
  │    └── CLI/Export
  └── Source of Truth Rules
       ├── PreRegistrationCheck
       ├── Execution Layer
       └── Shadow Monitor
```

## 最小先后顺序

### 第 1 批（先做）
- Domain Models
- System Invariants
- Provider Architecture
- CryptoAgents Adapter output contract
- Strategy Template / Validation contract

### 第 2 批
- PreRegistrationCheck
- Execution Compiler
- Investment State Machine contract

### 第 3 批
- Reactive runtime + Execution Layer
- CLI approval surface
- Export layer

### 第 4 批
- Shadow Monitor
- Emergency force-close
- Test hardening / replay / dry-run

## 每个模块的交付要求
- 目标职责
- 输入 schema
- 输出 schema
- 不负责的内容
- 依赖模块
- 可并行边界
