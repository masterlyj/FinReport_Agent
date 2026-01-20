# `demo/backend/` 开发者备忘录

## 1. 模块定义
**一句话**: FastAPI Web后端，提供配置管理、任务执行、实时日志的WebSocket API。

**核心文件**: `app.py` (31KB)

## 2. API端点

| 端点 | 方法 | 功能 |
| :--- | :--- | :--- |
| `/api/config` | POST | 设置配置或保存到文件 |
| `/api/config` | GET | 获取当前配置 |
| `/api/tasks` | POST | 设置采集/分析任务 |
| `/api/execution/start` | POST | 启动报告生成 |
| `/ws/logs` | WebSocket | 实时日志流 |
| `/api/outputs` | GET | 列出生成的报告文件 |

## 3. 核心流程

```
1. 前端POST配置 → /api/config → 保存到user_configs/
2. 前端POST任务列表 → /api/tasks → 更新config
3. 前端POST启动请求 → /api/execution/start → 后台asyncio.create_task()
4. 前端WebSocket连接 → /ws/logs → 实时接收日志
5. 执行完成 → 前端GET /api/outputs → 下载.docx/.pdf
```

## 4. 注意事项

| 项目 | 说明 |
| :--- | :--- |
| **CORS** | 支持前端跨域访问 |
| **后台任务** | 使用`asyncio.create_task()`异步执行 |
| **日志WebSocket** | 自定义Handler将日志推送到前端 |
| **配置持久化** | 保存到`user_configs/{timestamp}.yaml` |
