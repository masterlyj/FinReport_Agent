# FinReport_Agent 技术架构文档

## 📋 目录

- [1. 项目概述](#1-项目概述)
- [2. 系统架构](#2-系统架构)
- [3. 核心组件](#3-核心组件)
- [4. 数据流与执行流程](#4-数据流与执行流程)
- [5. 配置系统](#5-配置系统)
- [6. 使用方式](#6-使用方式)
- [7. 扩展指南](#7-扩展指南)

---

## 1. 项目概述

### 1.1 项目定位

FinReport_Agent 是一个**多智能体协作的金融研究报告自动生成系统**，能够从数据采集、分析到生成专业级报告的全流程自动化。

### 1.2 核心特性

- **多智能体协作**: DataCollector、DataAnalyzer、ReportGenerator 三大智能体协同工作
- **代码优先分析**: CAVM (Code Agent with Variable Memory) 架构，通过Python代码执行进行数据分析
- **VLM图表优化**: 视觉语言模型自动优化图表质量
- **断点续传**: Memory系统支持任务中断后恢复
- **多入口支持**: 命令行(CLI)和Web UI两种使用方式

### 1.3 技术栈

| 层级 | 技术 |
|------|------|
| 核心语言 | Python 3.10+ |
| 后端框架 | FastAPI |
| 前端框架 | React + Vite |
| LLM集成 | OpenAI兼容API (DeepSeek、Qwen等) |
| 数据处理 | Pandas, NumPy |
| 报告生成 | Python-docx, Pandoc |
| 异步执行 | Asyncio |

---

## 2. 系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         用户交互层                                 │
│  ┌──────────────────┐              ┌──────────────────┐          │
│  │   CLI入口        │              │   Web UI         │          │
│  │  run_report.py   │              │  React前端       │          │
│  └────────┬─────────┘              └────────┬─────────┘          │
└───────────┼──────────────────────────────────┼──────────────────┘
            │                                  │
            │ 直接导入                          │ HTTP/WebSocket
            ▼                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                         API层                                     │
│  ┌──────────────────┐              ┌──────────────────┐          │
│  │  CLI调用         │              │  FastAPI后端     │          │
│  │                  │              │  demo/backend/   │          │
│  └────────┬─────────┘              └────────┬─────────┘          │
└───────────┼──────────────────────────────────┼──────────────────┘
            │                                  │
            └──────────────┬───────────────────┘
                           │ 导入
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    核心业务逻辑层 (src/)                          │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │DataCollector│ │DataAnalyzer  │ │ReportGenerator│           │
│  │  数据采集     │ │  数据分析     │ │  报告生成     │           │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘           │
│         │                 │                 │                     │
│         └─────────────────┼─────────────────┘                     │
│                           ▼                                       │
│  ┌──────────────────────────────────────────────────┐            │
│  │              Memory (共享变量空间)                │            │
│  │  - 数据存储  - 任务映射  - 依赖关系  - 检查点     │            │
│  └──────────────────────────────────────────────────┘            │
│                           ▼                                       │
│  ┌──────────────────────────────────────────────────┐            │
│  │              Tools (工具库)                       │            │
│  │  financial/  macro/  industry/  web/             │            │
│  └──────────────────────────────────────────────────┘            │
│                           ▼                                       │
│  ┌──────────────────────────────────────────────────┐            │
│  │              Config (配置管理)                    │            │
│  │  - YAML配置  - 环境变量  - 默认值                 │            │
│  └──────────────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 目录结构

```
FinReport_Agent/
├── src/                           # 核心业务逻辑库
│   ├── agents/                    # 智能体模块
│   │   ├── base_agent.py          # 基础智能体类
│   │   ├── data_collector/        # 数据采集智能体
│   │   ├── data_analyzer/         # 数据分析智能体
│   │   ├── report_generator/      # 报告生成智能体
│   │   └── search_agent/          # 搜索智能体
│   ├── config/                    # 配置管理
│   │   ├── config.py              # 配置加载器
│   │   └── default_config.yaml    # 默认配置
│   ├── memory/                    # 记忆管理
│   │   └── variable_memory.py     # 共享变量空间
│   ├── tools/                     # 工具库
│   │   ├── financial/             # 财务数据工具
│   │   ├── macro/                 # 宏观经济工具
│   │   ├── industry/              # 行业数据工具
│   │   └── web/                   # 网络搜索工具
│   ├── utils/                     # 工具函数
│   │   ├── llm.py                 # LLM封装
│   │   ├── code_executor.py       # 代码执行器
│   │   ├── prompt_loader.py       # 提示词加载器
│   │   └── ...
│   └── template/                  # 报告模板
│       ├── company_outline.md     # 公司报告大纲
│       └── report_template.docx   # Word样式模板
│
├── demo/                          # Web演示
│   ├── backend/                   # FastAPI后端
│   │   └── app.py                 # API服务器
│   └── frontend/                  # React前端
│       ├── src/                   # 前端源码
│       ├── package.json
│       └── vite.config.js
│
├── run_report.py                  # CLI入口
├── main.py                        # 简单入口(未实现)
├── my_config.yaml                 # 用户配置
├── .env.example                   # 环境变量示例
└── requirements.txt               # Python依赖
```

### 2.3 架构设计原则

1. **分层清晰**: 用户层 → API层 → 业务逻辑层 → 数据层
2. **模块解耦**: src作为独立库，可被CLI和Web复用
3. **可扩展性**: 工具和智能体可独立扩展
4. **状态持久化**: Memory系统支持断点续传
5. **异步优先**: 使用asyncio实现高效并发

---

## 3. 核心组件

### 3.1 智能体系统 (Agents)

#### 3.1.1 BaseAgent (基础智能体)

**位置**: `src/agents/base_agent.py`

**职责**:
- 提供智能体的基础功能框架
- 管理代码执行器 (AsyncCodeExecutor)
- 实现检查点保存/加载
- 提供日志和工具管理

**核心方法**:
```python
class BaseAgent:
    async def async_run(input_data, echo, max_iterations, resume)
    def save_checkpoint(checkpoint_name)
    async def from_checkpoint(config, memory, agent_id)
```

**关键特性**:
- 每个智能体有唯一ID: `agent_{AGENT_NAME}_{uuid}`
- 独立工作目录: `{working_dir}/agent_working/{agent_id}`
- 支持代码执行环境隔离

#### 3.1.2 DataCollector (数据采集智能体)

**位置**: `src/agents/data_collector/data_collector.py`

**职责**:
- 根据任务自动选择合适的数据源
- 调用工具采集结构化和非结构化数据
- 将采集结果保存到Memory

**默认工具**:
- DeepSearchAgent (网络搜索)
- 所有financial/工具 (股票、财报)
- 所有macro/工具 (宏观经济)
- 所有industry/工具 (行业数据)

**执行流程**:
```
1. 接收任务描述
2. LLM分析任务，选择合适工具
3. 执行工具调用 (通过<execute>代码块)
4. 保存结果到Memory
5. 重复直到数据充足
```

**Prompt变量**:
- `{task}`: 采集任务
- `{api_descriptions}`: 工具API文档
- `{target_language}`: 输出语言

#### 3.1.3 DataAnalyzer (数据分析智能体)

**位置**: `src/agents/data_analyzer/data_analyzer.py`

**职责**:
- 对采集的数据进行分析
- 生成专业图表 (支持VLM优化)
- 生成分析报告

**核心能力**:
- **代码优先分析**: LLM生成Python代码进行分析
- **图表生成**: 自动生成专业级图表
- **VLM优化循环**: 
  1. LLM生成图表代码
  2. 执行生成图表
  3. VLM评估质量
  4. 根据反馈优化 (最多3轮)

**执行阶段**:
```
Phase 1: 数据分析
  - 获取Memory中的数据
  - 执行分析代码
  - 生成图表

Phase 2: 报告草稿
  - 整合分析结果
  - 生成文本报告
```

**代码执行器暴露的变量**:
```python
collect_data_list        # 采集的数据列表
get_existed_data(id)     # 获取指定数据
get_data_from_deep_search(query)  # 深度搜索
session_output_dir       # 图表输出目录
custom_palette           # 自定义配色方案
```

#### 3.1.4 ReportGenerator (报告生成智能体)

**位置**: `src/agents/report_generator/report_generator.py`

**职责**:
- 生成报告大纲
- 逐节撰写报告内容
- 生成封面、摘要、参考文献
- 渲染为Word/PDF格式

**执行阶段**:
```
Phase 1: 大纲生成
  - LLM生成报告大纲
  - VLM/LLM评估和优化

Phase 2: 章节撰写
  - 逐节生成内容
  - 引用Memory中的数据和图表

Phase 3: 后处理
  - 生成封面
  - 生成摘要和标题
  - 添加参考文献
  - 渲染为Word/PDF
```

**报告模板**:
- Markdown格式: 便于版本控制和预览
- Word模板: 控制最终输出样式
- Pandoc转换: Word → PDF

#### 3.1.5 DeepSearchAgent (搜索智能体)

**位置**: `src/agents/search_agent/search_agent.py`

**职责**:
- 多跳网络搜索
- 网页内容抓取
- 搜索结果验证和去重

**搜索引擎**:
- Serper (Google API)
- Bocha (中文搜索)
- Bing (requests/playwright)
- DuckDuckGo, Sogou

**输出格式**:
```python
DeepSearchResult(
    query="搜索查询",
    snippets=["片段1", "片段2"],
    pages=[ClickResult(...)],
    sources=["来源URL1", "来源URL2"]
)
```

### 3.2 Memory系统 (共享变量空间)

**位置**: `src/memory/variable_memory.py`

**职责**:
- 管理所有智能体的共享数据
- 维护任务映射和依赖关系
- 支持断点续传

**核心数据结构**:
```python
class Memory:
    log: List[str]                    # 操作日志
    data: List[ToolResult]            # 采集的数据
    dependency: Dict[str, List[str]]  # 依赖关系 (parent -> children)
    task_mapping: List[Dict]          # 任务映射
    data2embedding: Dict              # 数据嵌入 (语义搜索)
    generated_collect_tasks: List[str] # 生成的采集任务
    generated_analysis_tasks: List[str] # 生成的分析任务
```

**关键方法**:
```python
# 数据管理
add_data(tool_result)
get_collect_data(exclude_type=[])
search_data(query, top_k=5)

# 任务管理
add_task_mapping(...)
get_or_create_agent(...)
is_agent_finished(agent_id)

# 持久化
save(checkpoint_name='memory.pkl')
load(checkpoint_name='memory.pkl')
```

**数据流**:
```
DataCollector → add_data() → Memory.data
DataAnalyzer → get_collect_data() → Memory.data
ReportGenerator → search_data() → Memory.data
```

### 3.3 Tools系统 (工具库)

**位置**: `src/tools/`

**目录结构**:
```
tools/
├── base.py              # 工具基类
├── financial/           # 财务数据
│   ├── stock.py         # 股票数据
│   ├── company_statements.py  # 财报
│   └── market.py        # 市场数据
├── macro/               # 宏观经济
│   └── macro.py         # 宏观指标
├── industry/            # 行业数据
│   └── industry.py      # 行业指标
└── web/                 # 网络工具
    ├── base_search.py   # 搜索基类
    ├── web_crawler.py   # 爬虫
    └── search_engine_*.py  # 搜索引擎
```

**工具基类**:
```python
class Tool:
    name: str                      # 工具名称
    description: str               # 工具描述 (给LLM看)
    parameters: List[Dict]         # 参数定义
    
    async def api_function(**kwargs) -> List[ToolResult]
```

**自动注册机制**:
- 工具放在对应目录下自动被发现
- 通过 `get_tool_by_name(name)` 获取工具实例
- 通过 `get_tool_categories()` 获取分类列表

**ToolResult格式**:
```python
ToolResult(
    name="数据名称",
    description="数据描述",
    data=pd.DataFrame | dict | list,  # 实际数据
    source="数据来源"
)
```

### 3.4 Config系统 (配置管理)

**位置**: `src/config/config.py`

**配置加载优先级**:
```
1. default_config.yaml (默认值)
2. my_config.yaml (用户配置)
3. config_dict (运行时参数，最高优先级)
```

**环境变量替换**:
```yaml
# 在YAML中使用 ${VAR_NAME}
llm_config_list:
  - model_name: "${DS_MODEL_NAME}"
    api_key: "${DS_API_KEY}"
    base_url: "${DS_BASE_URL}"
```

**核心配置项**:
```yaml
# 目标配置
target_name: "公司名称"
stock_code: "000001"
target_type: "financial_company"  # financial_company | macro | industry | general
output_dir: "./outputs/my-research"
language: "en"  # en | zh

# 模板路径
reference_doc_path: 'src/template/report_template.docx'
outline_template_path: 'src/template/company_outline.md'

# 缓存控制
use_collect_data_cache: True
use_analysis_cache: True
use_report_outline_cache: True
use_full_report_cache: True
use_post_process_cache: True

# LLM配置
llm_config_list:
  - model_name: "deepseek-chat"
    api_key: "sk-xxx"
    base_url: "https://api.deepseek.com/v1"
    generation_params:
      temperature: 0.7
      max_tokens: 32768
```

### 3.5 Utils系统 (工具函数)

**位置**: `src/utils/`

**核心模块**:

| 模块 | 功能 |
|------|------|
| `llm.py` | LLM封装，支持OpenAI兼容API |
| `code_executor.py` | 异步代码执行器，沙箱环境 |
| `prompt_loader.py` | YAML提示词加载器 |
| `logger.py` | 日志系统，支持agent context |
| `index_builder.py` | 向量索引构建 (语义搜索) |
| `figure_helper.py` | 图表辅助函数 |
| `helper.py` | 通用工具函数 |

**AsyncCodeExecutor特性**:
- 安全的代码执行环境
- 变量隔离
- 支持设置/获取变量
- 自动保存执行状态

---

## 4. 数据流与执行流程

### 4.1 整体执行流程

```
┌─────────────────────────────────────────────────────────────┐
│ 1. 初始化阶段                                                 │
│    - 加载配置 (Config)                                       │
│    - 初始化Memory                                            │
│    - 生成/加载任务 (collect_tasks, analysis_tasks)           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. 数据采集阶段 (Priority 1)                                 │
│    - 并发执行多个DataCollector                                │
│    - 调用工具采集数据                                         │
│    - 保存结果到Memory                                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. 数据分析阶段 (Priority 2)                                 │
│    - 并发执行多个DataAnalyzer                                │
│    - 从Memory读取数据                                         │
│    - 执行分析代码                                             │
│    - 生成图表和报告草稿                                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. 报告生成阶段 (Priority 3)                                 │
│    - 执行ReportGenerator                                     │
│    - 生成大纲 → 撰写章节 → 后处理                             │
│    - 渲染为Word/PDF                                          │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 数据流详解

#### 4.2.1 数据采集流

```
User Task (my_config.yaml)
    ↓
DataCollector.async_run()
    ↓
LLM分析任务，选择工具
    ↓
<execute>代码块调用工具
    ↓
Tool.api_function() → ToolResult
    ↓
Memory.add_data(ToolResult)
    ↓
Memory.data[] (共享存储)
```

#### 4.2.2 数据分析流

```
Analysis Task
    ↓
DataAnalyzer.async_run()
    ↓
Memory.get_collect_data()
    ↓
<execute>分析代码
    ↓
生成图表 (matplotlib/plotly)
    ↓
VLM评估图表质量
    ↓
优化图表 (最多3轮)
    ↓
保存图表 + 分析文本
    ↓
Memory.add_data(AnalysisResult)
```

#### 4.2.3 报告生成流

```
Report Task
    ↓
ReportGenerator.async_run()
    ↓
Phase 1: 大纲生成
    - LLM生成大纲
    - 评估和优化
    ↓
Phase 2: 章节撰写
    - 逐节生成内容
    - 引用数据和图表
    ↓
Phase 3: 后处理
    - 生成封面
    - 生成摘要
    - 添加参考文献
    ↓
渲染输出
    - Markdown (预览)
    - Word (docx)
    - PDF (pandoc)
```

### 4.3 断点续传机制

**检查点层级**:
```
Memory Level:
  - memory.pkl (全局状态)
  - task_mapping (任务映射)

Agent Level:
  - agent_working/{agent_id}/.cache/latest.pkl
  - agent_working/{agent_id}/.executor_cache/state.dill

Resume Flow:
  1. Memory.load() → 恢复全局状态
  2. 遍历task_mapping → 获取agent_id
  3. Agent.from_checkpoint() → 恢复agent状态
  4. 跳过已完成的任务
  5. 继续执行未完成任务
```

**配置控制**:
```yaml
use_collect_data_cache: True
use_analysis_cache: True
use_report_outline_cache: True
use_full_report_cache: True
use_post_process_cache: True
```

---

## 5. 配置系统

### 5.1 配置文件结构

**my_config.yaml**:
```yaml
# ===== 目标配置 =====
target_name: "公司名称"
stock_code: "000001"
target_type: "financial_company"
output_dir: "./outputs/my-research"
language: "en"

# ===== 模板路径 =====
reference_doc_path: 'src/template/report_template.docx'
outline_template_path: 'src/template/company_outline.md'

# ===== 自定义任务 (可选) =====
custom_collect_tasks:
  - "采集财务报表"
  - "获取股价数据"

custom_analysis_tasks:
  - "分析营收趋势"
  - "评估盈利能力"

# ===== 缓存设置 =====
use_collect_data_cache: true
use_analysis_cache: true
use_report_outline_cache: true
use_full_report_cache: true
use_post_process_cache: true

# ===== LLM配置 =====
llm_config_list:
  - model_name: "${DS_MODEL_NAME}"
    api_key: "${DS_API_KEY}"
    base_url: "${DS_BASE_URL}"
    generation_params:
      temperature: 0.7
      max_tokens: 32768
      top_p: 0.95
```

**.env**:
```bash
# LLM (主推理模型)
DS_MODEL_NAME="deepseek-chat"
DS_API_KEY="sk-your-key"
DS_BASE_URL="https://api.deepseek.com/v1"

# VLM (视觉语言模型)
VLM_MODEL_NAME="qwen-vl-max"
VLM_API_KEY="sk-your-key"
VLM_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"

# Embedding (嵌入模型)
EMBEDDING_MODEL_NAME="text-embedding-v3"
EMBEDDING_API_KEY="sk-your-key"
EMBEDDING_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"

# Web Search (可选)
SERPER_API_KEY="your-serper-key"
BOCHAAI_API_KEY="your-bocha-key"
```

### 5.2 目标类型说明

| target_type | 适用场景 | 默认工具 |
|-------------|----------|----------|
| `financial_company` | 上市公司研究 | financial + market tools |
| `macro` | 宏观经济分析 | macro indicators |
| `industry` | 行业/板块研究 | industry + macro tools |
| `general` | 通用深度研究 | web search only |

### 5.3 Prompt系统

**目录结构**:
```
src/agents/
├── data_collector/prompts/
│   └── prompts.yaml
├── data_analyzer/prompts/
│   ├── financial_prompts.yaml
│   └── general_prompts.yaml
├── report_generator/prompts/
│   ├── financial_company_prompts.yaml
│   ├── financial_industry_prompts.yaml
│   ├── financial_macro_prompts.yaml
│   └── general_prompts.yaml
└── search_agent/prompts/
    └── general_prompts.yaml
```

**Prompt加载**:
```python
from src.utils.prompt_loader import get_prompt_loader

# 加载prompt
loader = get_prompt_loader('data_analyzer', report_type='financial')
prompt = loader.get_prompt('data_analysis', 
    current_time="2024-12-01",
    user_query="分析营收趋势",
    data_info="可用数据...",
    target_language="中文"
)
```

**自定义Prompt**:
1. 在对应目录创建 `my_custom_prompts.yaml`
2. 定义prompt模板
3. 设置 `target_type: 'my_custom'` 加载

---

## 6. 使用方式

### 6.1 命令行方式 (CLI)

**快速开始**:
```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑.env，填入API密钥

# 2. 配置研究目标
# 编辑my_config.yaml

# 3. 运行报告生成
python run_report.py

# 4. 从断点恢复
python run_report.py --resume
```

**并发控制**:
```bash
# 设置最大并发任务数
export MAX_CONCURRENT=3
python run_report.py

# 或在代码中设置
python run_report.py --max-concurrent 3
```

### 6.2 Web UI方式

**启动后端**:
```bash
cd demo/backend
python app.py
# 服务运行在 http://localhost:8000
```

**启动前端**:
```bash
cd demo/frontend
npm install
npm run dev
# 服务运行在 http://localhost:3000
```

**Web功能**:
- 配置管理: 创建/加载/保存配置
- 任务管理: 自定义采集和分析任务
- 执行监控: 实时查看日志和进度
- 报告浏览: 预览和下载生成的报告

### 6.3 API方式

**示例: 使用FastAPI后端**:
```python
import requests

# 1. 设置配置
config = {
    "target_name": "公司名称",
    "stock_code": "000001",
    "output_dir": "outputs/demo",
    "llm_configs": [...],
    ...
}
requests.post("http://localhost:8000/api/config", json=config)

# 2. 设置任务
tasks = {
    "collect_tasks": [...],
    "analysis_tasks": [...]
}
requests.post("http://localhost:8000/api/tasks", json=tasks)

# 3. 启动执行
requests.post("http://localhost:8000/api/execution/start", 
              json={"resume": False})

# 4. 查看状态
status = requests.get("http://localhost:8000/api/execution/status")

# 5. 获取报告列表
reports = requests.get("http://localhost:8000/api/reports")
```

**WebSocket日志流**:
```python
import asyncio
import websockets

async def stream_logs():
    uri = "ws://localhost:8000/ws/logs"
    async with websockets.connect(uri) as websocket:
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            if data["type"] == "log":
                print(f"[{data['agent_id']}] {data['message']}")

asyncio.run(stream_logs())
```

---

## 7. 扩展指南

### 7.1 添加新工具

**步骤**:
1. 在 `src/tools/` 对应目录创建工具文件
2. 继承 `Tool` 基类
3. 实现 `api_function` 方法
4. 工具自动被发现和注册

**示例**:
```python
# src/tools/financial/my_custom_tool.py
from src.tools.base import Tool, ToolResult

class MyCustomTool(Tool):
    def __init__(self):
        super().__init__(
            name="My Custom Tool",
            description="工具描述，LLM会读取",
            parameters=[
                {
                    "name": "stock_code",
                    "type": "str",
                    "description": "股票代码",
                    "required": True
                }
            ]
        )
    
    async def api_function(self, stock_code: str):
        # 获取数据
        data = await self._fetch_data(stock_code)
        
        return [
            ToolResult(
                name=f"{stock_code}_data",
                description="数据描述",
                data=data,
                source="数据来源"
            )
        ]
```

### 7.2 添加新智能体

**步骤**:
1. 在 `src/agents/` 创建智能体目录
2. 继承 `BaseAgent`
3. 实现 `_prepare_init_prompt` 和 `_prepare_executor`
4. 注册到 `_AGENT_REGISTRY`

**示例**:
```python
# src/agents/my_agent/my_agent.py
from src.agents.base_agent import BaseAgent, register_agent_class

@register_agent_class
class MyAgent(BaseAgent):
    AGENT_NAME = 'my_agent'
    AGENT_DESCRIPTION = '我的智能体描述'
    NECESSARY_KEYS = ['task']
    
    def __init__(self, config, tools=[], use_llm_name="deepseek-chat", 
                 enable_code=True, memory=None, agent_id=None):
        super().__init__(config, tools, use_llm_name, enable_code, memory, agent_id)
        
        # 加载prompt
        from src.utils.prompt_loader import get_prompt_loader
        self.prompt_loader = get_prompt_loader('my_agent')
        self.MY_PROMPT = self.prompt_loader.get_prompt('my_prompt')
    
    async def _prepare_init_prompt(self, input_data: dict) -> list[dict]:
        task = input_data.get('task')
        prompt = self.MY_PROMPT.format(task=task)
        return [{"role": "user", "content": prompt}]
    
    async def _prepare_executor(self):
        # 设置代码执行器变量
        self.code_executor.set_variable("my_helper", self._my_helper)
    
    def _my_helper(self, arg):
        # 辅助函数
        return result
```

### 7.3 自定义报告模板

**大纲模板** (`src/template/my_outline.md`):
```markdown
# 执行摘要
关键指标、投资观点、评级

# 公司概况
- 业务描述和历史
- 管理层和治理
- 股东结构

# 行业分析
- 市场规模和增长
- 竞争格局

# 财务分析
- 营收和盈利趋势
- 资产负债表分析
- 现金流分析

# 估值
- 可比公司分析
- DCF估值
- 目标价格

# 风险
- 主要风险和缓解措施
```

**Word样式模板**:
1. 复制 `src/template/report_template.docx`
2. 在Word中编辑样式:
   - Heading 1/2/3: 标题样式
   - Normal: 正文样式
   - Table: 表格样式
3. 在配置中指定新模板路径

### 7.4 自定义图表样式

**修改配色方案**:
```python
# 在 DataAnalyzer._prepare_executor() 中
custom_palette = [
    "#003366",  # 深蓝
    "#0066CC",  # 中蓝
    "#66B2FF",  # 浅蓝
    "#CCE5FF",  # 极浅蓝
    "#E6F2FF",  # 淡蓝
]
self.code_executor.set_variable("custom_palette", custom_palette)
```

**调整VLM优化轮次**:
```python
# 在 _draw_single_chart() 中
chart_code, chart_name = await self._draw_single_chart(
    task=...,
    max_iterations=5  # 增加优化轮次
)
```

### 7.5 添加新的搜索引擎

**步骤**:
1. 在 `src/tools/web/` 创建搜索引擎文件
2. 继承 `BaseSearchEngine`
3. 实现 `search()` 方法
4. 自动注册到搜索系统

**示例**:
```python
# src/tools/web/my_search.py
from src.tools.web.base_search import BaseSearchEngine, SearchResult

class MySearchEngine(BaseSearchEngine):
    def __init__(self):
        super().__init__(
            name="My Search",
            description="我的搜索引擎"
        )
    
    async def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        # 实现搜索逻辑
        results = await self._fetch_results(query, num_results)
        
        return [
            SearchResult(
                title=r.title,
                url=r.url,
                snippet=r.snippet,
                source="my_search"
            )
            for r in results
        ]
```

---

## 8. 最佳实践

### 8.1 性能优化

1. **并发控制**:
   - 使用 `MAX_CONCURRENT` 环境变量控制并发数
   - 优先级分组: 采集 → 分析 → 报告

2. **缓存策略**:
   - 开启所有缓存选项
   - 定期清理旧缓存

3. **内存管理**:
   - 使用 `exclude_type` 过滤不需要的数据
   - 及时清理临时文件

### 8.2 调试技巧

1. **查看日志**:
   ```bash
   # 查看agent日志
   tail -f outputs/{target_name}/logs/agent_{agent_id}.log
   
   # 查看主日志
   tail -f outputs/{target_name}/logs/main.log
   ```

2. **检查Memory状态**:
   ```python
   from src.memory import Memory
   from src.config import Config
   
   config = Config('my_config.yaml')
   memory = Memory(config)
   memory.load()
   
   print(f"数据数量: {len(memory.data)}")
   print(f"任务数量: {len(memory.task_mapping)}")
   ```

3. **单步执行**:
   ```python
   # 只执行数据采集
   from src.agents import DataCollector
   
   collector = DataCollector(config=config, memory=memory)
   await collector.async_run(input_data={...})
   ```

### 8.3 错误处理

1. **常见错误**:
   - API密钥未配置 → 检查 `.env` 文件
   - 网络超时 → 增加重试次数
   - 内存不足 → 减少并发数

2. **恢复机制**:
   - 使用 `--resume` 从断点恢复
   - 检查 `memory.pkl` 是否损坏
   - 清理缓存重新开始

---

## 9. 附录

### 9.1 环境变量清单

| 变量名 | 说明 | 必需 |
|--------|------|------|
| `DS_MODEL_NAME` | LLM模型名称 | 是 |
| `DS_API_KEY` | LLM API密钥 | 是 |
| `DS_BASE_URL` | LLM API地址 | 是 |
| `VLM_MODEL_NAME` | VLM模型名称 | 是 |
| `VLM_API_KEY` | VLM API密钥 | 是 |
| `VLM_BASE_URL` | VLM API地址 | 是 |
| `EMBEDDING_MODEL_NAME` | 嵌入模型名称 | 是 |
| `EMBEDDING_API_KEY` | 嵌入API密钥 | 是 |
| `EMBEDDING_BASE_URL` | 嵌入API地址 | 是 |
| `SERPER_API_KEY` | Serper搜索密钥 | 否 |
| `BOCHAAI_API_KEY` | Bocha搜索密钥 | 否 |
| `MAX_CONCURRENT` | 最大并发数 | 否 |

### 9.2 输出目录结构

```
outputs/{target_name}/
├── agent_working/              # 智能体工作目录
│   ├── agent_data_collector_xxx/
│   │   ├── .cache/
│   │   └── .executor_cache/
│   ├── agent_data_analyzer_xxx/
│   │   ├── .cache/
│   │   ├── .executor_cache/
│   │   └── images/            # 生成的图表
│   └── agent_report_generator_xxx/
│       └── .cache/
├── memory/                     # Memory检查点
│   └── memory.pkl
├── logs/                       # 日志文件
│   ├── main.log
│   └── agent_*.log
├── final_report/               # 最终报告
│   ├── report.md
│   ├── report.docx
│   └── report.pdf
└── config.json                 # 配置快照
```

### 9.3 关键文件索引

| 文件路径 | 说明 |
|---------|------|
| `run_report.py` | CLI入口 |
| `demo/backend/app.py` | FastAPI后端 |
| `src/agents/base_agent.py` | 智能体基类 |
| `src/agents/data_collector/data_collector.py` | 数据采集智能体 |
| `src/agents/data_analyzer/data_analyzer.py` | 数据分析智能体 |
| `src/agents/report_generator/report_generator.py` | 报告生成智能体 |
| `src/memory/variable_memory.py` | Memory系统 |
| `src/config/config.py` | 配置管理 |
| `src/utils/code_executor.py` | 代码执行器 |
| `src/utils/prompt_loader.py` | Prompt加载器 |
| `src/tools/base.py` | 工具基类 |

---

## 10. 常见问题 (FAQ)

**Q1: 如何更换LLM提供商？**

A: 修改 `.env` 文件中的API配置，确保模型名称和API地址正确。例如使用OpenRouter:
```bash
DS_MODEL_NAME="openai/gpt-4o"
DS_API_KEY="sk-or-xxx"
DS_BASE_URL="https://openrouter.ai/api/v1"
```

**Q2: 如何减少API调用成本？**

A: 
1. 开启所有缓存选项
2. 减少 `max_iterations` 参数
3. 使用更便宜的模型进行初步分析

**Q3: 如何处理中文报告？**

A: 在 `my_config.yaml` 中设置:
```yaml
language: "zh"
outline_template_path: 'src/template/company_outline_zh.md'
```

**Q4: 如何添加新的数据源？**

A: 参考 [7.1 添加新工具](#71-添加新工具)，创建自定义工具类。

**Q5: 报告生成失败如何调试？**

A:
1. 检查 `logs/` 目录下的日志文件
2. 使用Web UI查看实时日志
3. 单独执行失败的智能体进行调试

---
示例任务：
custom_collect_tasks:
  - "资产负债表, 利润表, 现金流量表三大财务报表"
  - "股票基本信息以及股价数据"
  - "股东结构"
  - "投资评级"
  - "公司市销率, 净资产收益率(ROE), 市盈率, 市净率"
  - "公司主要竞争对手情况"
  - "指数数据: 沪深300指数日数据, 恒生指数日数据, 上证指数日数据, 纳斯达克指数日数据"
custom_analysis_tasks:
  - "梳理公司发展历程、关键里程碑事件及当前核心主营业务范围"
  - "分析创始团队及高管背景，梳理股权结构及主要股东情况"
  - "梳理公司上市前的融资轮次、金额及主要投资方"
  - "分析历年营收趋势、各业务板块占比变化及增长驱动因素"
  - "评估公司盈利能力（ROE、毛利率、净利率）及运营效率（各项周转率）"
  - "分析公司偿债能力（资产负债率、流动比率）及现金流结构与健康度"
  - "进行同行业竞争对手对比分析，评估行业地位及核心竞争力（技术/品牌/渠道）"
  - "复盘近5年股价走势与成交量，分析关键事件（政策/财报/技术）对股价的影响"
  - "整理历史三大财务报表，预测未来两年核心财务数据，并进行估值分析"