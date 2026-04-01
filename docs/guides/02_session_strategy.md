# Codex 会话策略

## 推荐会话粒度
- 1 session = 1 module = 1 deliverable

例如：
- `execution_compiler`：先只做 schema + compile 函数
- 下一轮再做 compiler tests
- 再下一轮做 CLI wiring

## 并行方式
可以开多个独立 session：
- Session A: decision/
- Session B: validation/
- Session C: execution/compiler/
- Session D: contracts/

每个 session 都只挂载自己的 contract + prompt。

## 合并前要求
- 先以 contract 为准核对职责边界
- 确认没有跨模块偷改行为
- 跑本模块最低测试集合
