# PRD 开发验收与对接包

这套文件用于解决并行开发时最容易出的问题：
- 线程彼此隔离，导致接口假设不一致
- 一个 wave 内各线程各自“完成”了，但组合后无法工作
- 下一 wave 开始时，不知道上一 wave 的真实完成度、风险和遗留项

## 使用原则
1. **每个线程结束时必须做线程内验收**
2. **每个 Wave 结束时必须做 Wave 内验收**
3. **每个线程交付前必须产出线程间对接文件**
4. **每个 Wave 结束后必须产出 Wave 间对接文件**
5. 未通过当前 Wave gate，不建议进入下一 Wave

## 目录
- `00_overview/`：整体流程与 DoD
  - `04_phase1_go_no_go.md`：Phase 1 上线清单模板
  - `05_phase1_go_no_go_instance.md`：Phase 1 当前状态实例
  - `06_phase1_full_chain_go_no_go.md`：Phase 1 全链路真实执行上线清单
  - `07_phase1_preproduction_go_no_go.md`：Phase 1 预生产上线清单
- `01_thread_acceptance/`：线程内验收模板
- `02_wave_acceptance/`：Wave 内验收模板
- `03_thread_handoff/`：线程间对接模板
- `04_wave_handoff/`：Wave 间对接模板
- `05_prefilled_wave_packets/`：按 Wave 预填好的验收包

## 推荐节奏
- Thread 完成一个 prompt → 填 01 + 03
- Wave 内所有 thread 完成 → 填 02
- Wave gate 通过 → 填 04，再开下一 Wave
