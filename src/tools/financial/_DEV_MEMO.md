# Tools子模块开发者备忘录

由于tools子模块(financial/macro/industry/web)结构相似，此处提供统一说明。

## financial/ - 财务数据工具

**文件**: `stock.py`, `company_statements.py`, `market.py`  
**数据源**: AkShare, EFinance  
**核心工具**:
- StockInfo: 股票基本信息
- CompanyStatements: 三大财务报表(利润表/资产负债表/现金流量表)
- MarketData: 市场指标(市盈率/ROE/市净率)

## macro/ - 宏观经济工具

**文件**: `macro.py`  
**数据源**: AkShare  
**核心工具**:
- MacroIndicators: GDP、CPI、PMI等宏观经济指标

## industry/ - 行业数据工具

**文件**: `industry.py`  
**数据源**: AkShare  
**核心工具**:
- IndustryData: 行业板块数据、行业指数

## web/ - 网络工具

**文件**: `base_search.py`, `search_engine_*.py`, `web_crawler.py`  
**核心工具**:
- SerperSearch: Google搜索API
- BingSearch: Bing搜索(requests)
- BochaSearch: 中文搜索引擎
- Click: 网页内容抓取(Crawl4AI)

## 共性注意事项

| 项目 | 说明 |
| :--- | :--- |
| **API Key** | Serper/Bocha需要在.env配置API_KEY |
| **中文数据** | AkShare返回DataFrame列名为中文，需做映射 |
| **异常处理** | 所有工具通过@async_retry自动重试，失败返回空列表 |
| **ToolResult格式** | 统一返回`List[ToolResult]`，name+description+data+source |
