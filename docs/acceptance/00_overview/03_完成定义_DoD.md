# 完成定义（Definition of Done）

一个模块只有同时满足下面 7 条，才能算“完成”：

1. 仅修改允许路径
2. 满足该模块 implementation contract
3. 满足全局 invariants
4. 至少有一个 happy path 测试或可验证演示
5. 输出对象/接口已冻结到 handoff 文件
6. 已知限制、TODO、blocker 已显式记录
7. 交付说明包含 commit / changed files / commands run / evidence

一个 Wave 只有同时满足下面 6 条，才能进入下一 Wave：

1. Wave 内所有线程都通过线程内验收
2. Wave 内所有线程都提交了线程间 handoff
3. Wave 内交叉依赖已经对齐
4. 最小跨模块流程可运行或可验证
5. 未解决问题已被明确降级为下一 Wave 的已知项
6. 已产出 wave-to-wave handoff 包
