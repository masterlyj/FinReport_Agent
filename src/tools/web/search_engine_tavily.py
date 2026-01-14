"""
Tavily Search Engine (AI-powered search)

官网: https://tavily.com
免费额度: 1000 searches/月
优点: AI优化搜索结果，支持深度研究
"""

from typing import List
import os

from ..base import Tool, ToolResult
from .base_search import SearchResult
from ...utils.logger import get_logger

logger = get_logger()


class TavilySearch(Tool):
    """
    Tavily AI搜索引擎
    
    特点:
    - AI优化的搜索结果
    - 支持深度研究模式
    - 1000次/月免费额度
    """

    def __init__(self):
        super().__init__(
            name="Tavily AI Search",
            description="AI-powered search engine for research. Excellent for comprehensive answers. 1000 free searches/month.",
            parameters=[{
                "name": "query", 
                "type": "str", 
                "description": "Search keywords (支持中英文)", 
                "required": True
            }],
        )

        self.backend = 'tavily'
        self.type = 'tool_search'
        
        api_key = os.getenv("TAVILY_API_KEY", "")
        if not api_key:
            logger.warning("TAVILY_API_KEY is not set; Tavily requests may fail.")
            print("Warning: TAVILY_API_KEY is not set. Please configure it in .env file.")
        self.api_key = api_key

    async def api_function(self, query: str) -> List[SearchResult]:
        """
        Execute Tavily AI search.

        Args:
            query: Search keywords

        Returns:
            A list of SearchResult entries
        """
        if not self.api_key:
            logger.error("TavilySearch: API key not configured")
            print("Error: TAVILY_API_KEY not configured. Skipping search.")
            return []

        try:
            from tavily import TavilyClient
            
            logger.info(f"TavilySearch: Searching for '{query}'")
            
            # 创建 Tavily 客户端
            client = TavilyClient(api_key=self.api_key)
            
            # 执行搜索
            # search_depth: "basic" 或 "advanced"
            response = client.search(
                query=query,
                search_depth="basic",
                max_results=10,
                include_answer=False,  # 不需要AI生成的答案
                include_raw_content=False,  # 不需要原始内容
            )
            
            # 检查结果
            if not response or 'results' not in response:
                logger.warning(f"TavilySearch: No results found for query: {query}")
                return []

            results = response['results']
            
            if not results:
                logger.info(f"TavilySearch: No results found for query: {query}")
                return []

            # 转换为 SearchResult 格式
            result_list = []
            for i, item in enumerate(results):
                try:
                    title = item.get('title', '')
                    link = item.get('url', '')
                    snippet = item.get('content', '')
                    score = item.get('score', 0)

                    if title and link:  # 至少要有标题和链接
                        result_list.append(SearchResult(
                            query=query,
                            name=title,
                            description=snippet,
                            link=link,
                            data=[{
                                'title': title,
                                'link': link,
                                'snippet': snippet,
                                'score': score,
                                'position': i + 1
                            }],
                            source=f'{title}\n{link}'
                        ))
                except Exception as e:
                    logger.warning(f"TavilySearch: Failed to parse result item: {e}")
                    continue

            logger.info(f"TavilySearch: Found {len(result_list)} results")
            
            return result_list

        except ImportError:
            logger.error("TavilySearch: tavily-python library not installed")
            print("Error: Please install: pip install tavily-python")
            return []
        except Exception as e:
            logger.error(f"TavilySearch: Unexpected error: {type(e).__name__}: {e}")
            print(f"Error: TavilySearch failed: {e}")
            return []


if __name__ == "__main__":
    # 测试代码
    import asyncio
    
    async def test():
        search_engine = TavilySearch()
        results = await search_engine.api_function("浪潮信息 服务器 市场份额")
        
        print(f"\n找到 {len(results)} 条结果:\n")
        for i, result in enumerate(results[:3], 1):
            print(f"{i}. {result.name}")
            print(f"   {result.link}")
            print(f"   {result.description[:100] if result.description else 'No description'}...")
            print()
    
    asyncio.run(test())
