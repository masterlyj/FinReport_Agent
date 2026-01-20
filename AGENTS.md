# 智能体（AI Agent）相关说明
## 🛠 操作命令

### 后端（Python 语言）
- **安装依赖**
  - 推荐方式：`uv sync`（项目已使用 `uv.lock` 文件锁定依赖版本）
  - 备选方式：`pip install -r requirements.txt`（需先生成该依赖清单文件）
- **运行命令行工具**：`python run_report.py`
- **启动 API 服务**：`python demo/backend/app.py`
- **代码检查**
  - `ruff check .`（Python 代码检查工具，推荐使用）
  - `flake8`（若项目已配置该工具，可作为备选方案）

### 前端（React 框架）
- **安装依赖**：`cd demo/frontend && npm install`
- **启动开发服务器**：`cd demo/frontend && npm run dev`
- **构建生产环境包**：`cd demo/frontend && npm run build`

## 🧪 测试说明
- **运行完整测试套件**：`pytest`
- **运行单个测试文件**：`pytest tests/path/to/test_file.py`（示例：`pytest tests/agents/test_data_analyzer.py`）
- **文件命名规范**：测试文件必须以 `test_` 开头（示例：`test_config.py`）
- **测试规则**：`src/` 目录下新增的所有核心功能，都必须在 `tests/` 目录中编写对应的单元测试

## 🏗 目录结构说明

### 核心逻辑层（`src/` 目录）
- **`src/agents`**：存放各类智能体的具体实现代码
  - `base_agent.py`：所有智能体的基类，提供基础功能与接口定义
  - `data_collector/`：负责获取外部数据的智能体模块
  - `data_analyzer/`：负责数据分析并生成图表的智能体模块（支持代码执行功能）
  - `report_generator/`：负责生成最终报告的智能体模块
  - `search_agent/`：负责网络深度搜索的智能体模块 (DeepSearch)
- **`src/tools`**：智能体可调用的工具定义目录
  - `financial/`：股票与财务报表相关工具
  - `macro/`、`industry/`：特定领域的数据工具
  - `web/`：搜索引擎与网页爬虫工具
- **`src/memory`**：智能体共享状态管理目录
  - `variable_memory.py`：负责智能体之间的数据持久化与共享
- **`src/config`**：配置管理目录
  - `config.py`：从 `default_config.yaml` 加载默认配置，并支持通过 `my_config.yaml` 文件覆盖默认配置

### Web 演示项目（`demo/` 目录）
- **`demo/backend`**：基于 FastAPI 框架构建的后端服务，提供智能体功能接口
- **`demo/frontend`**：基于 React + Vite 构建的前端用户界面

## 🚨 代码规范

### Python 语言规范
- **类型注解**：**强制要求**。所有函数必须添加类型注解（示例：`def func(x: int) -> str:`）
- **异步编程**：所有 I/O 密集型操作必须使用 `async/await` 语法。智能体默认设计为异步运行模式
- **数据验证**：使用 Pydantic 模型进行数据验证与模式定义，尤其适用于 API 响应数据和配置文件解析
- **异常处理**：遵循“快速失败”原则。禁止使用无指定异常类型的 `try-except` 语句，应捕获具体异常；开发阶段允许未捕获的异常向上抛出
- **文档字符串**：公开方法与类需使用 Google 风格的文档字符串

### 前端代码规范
- **技术框架**：使用 React 18 及以上版本，采用函数式组件与 Hooks 进行开发
- **状态管理**：使用 Context API 管理全局状态（示例：`LanguageContext` 语言上下文）
- **样式方案**：使用标准 CSS 或 Tailwind CSS（具体可参考项目根目录下的 `index.css` 文件）