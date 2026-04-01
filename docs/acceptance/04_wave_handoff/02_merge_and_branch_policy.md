# Merge 与分支策略

## 线程级
- 一个 prompt 一个分支
- 未完成 thread acceptance，不允许合并
- 未提交 thread handoff，不建议下游开工

## Wave 级
- 同一 Wave 的线程先分别完成
- Wave gate 通过后，再做集中集成合并
- 不建议“边开发边跨 Wave 混合合并”

## 推荐流程
1. thread branch 完成模块
2. 填线程内验收
3. 填线程间 handoff
4. 进入 wave integration branch
5. 做 wave gate
6. 通过后合并到主开发分支
7. 填 wave-to-wave handoff
