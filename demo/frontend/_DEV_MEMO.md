# `demo/frontend/` 开发者备忘录

## 1. 模块定义
**一句话**: React + Vite前端界面，提供可视化配置、任务管理、执行监控、报告预览。

**技术栈**: React 18 + Vite + Ant Design

## 2. 核心功能

| 页面/组件 | 功能 |
| :--- | :--- |
| 配置管理 | 创建/加载/保存研究配置(target_name, stock_code等) |
| 任务编辑 | 可视化编辑collect_tasks和analysis_tasks |
| 执行控制 | 启动/停止报告生成，显示进度 |
| 日志查看 | WebSocket实时显示Agent执行日志 |
| 报告预览 | 下载.docx/.pdf文件 |

## 3. 目录结构

```
frontend/
├── src/
│   ├── components/    # React组件
│   ├── pages/         # 页面路由
│   ├── services/      # API调用封装
│   ├── App.tsx        # 主应用
│   └── main.tsx       # 入口
├── package.json
└── vite.config.js
```

## 4. 启动方式

```bash
cd demo/frontend
npm install
npm run dev    # 开发服务器(默认http://localhost:3000)
npm run build  # 生产构建
```

## 5. 注意事项

| 项目 | 说明 |
| :--- | :--- |
| **API Base URL** | 默认`http://localhost:8000`，可通过环境变量配置 |
| **WebSocket** | 连接`ws://localhost:8000/ws/logs` |
| **依赖** | 需要后端先启动(python demo/backend/app.py) |
