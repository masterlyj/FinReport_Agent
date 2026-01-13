"""
SerpAPI Search Engine (推荐作为主搜索引擎)

官网: https://serpapi.com
免费额度: 250 searches/月
优点: Google搜索结果质量高，中文支持好
"""

from typing import List
import os
from serpapi import GoogleSearch

from ..base import Tool, ToolResult
from .base_search import SearchResult
from ...utils.logger import get_logger

logger = get_logger()


class SerpAPISearch(Tool):
    """
    SerpAPI 搜索引擎（推荐）
    
    使用 Google 搜索结果，质量高，中文友好
    免费额度: 250次/月
    """

    def __init__(self):
        super().__init__(
            name="SerpAPI Google Search",
            description="High-quality Google search via SerpAPI. Excellent for Chinese queries. 250 free searches/month.",
            parameters=[{
                "name": "query", 
                "type": "str", 
                "description": "Search keywords (支持中英文)", 
                "required": True
            }],
        )

        self.backend = 'serpapi'
        self.type = 'tool_search'
        
        api_key = os.getenv("SERPAPI_API_KEY", "")
        if not api_key:
            logger.warning("SERPAPI_API_KEY is not set; SerpAPI requests may fail.")
            print("Warning: SERPAPI_API_KEY is not set. Please configure it in .env file.")
        self.api_key = api_key

    async def api_function(self, query: str) -> List[ToolResult]:
        """
        Execute SerpAPI Google search.

        Args:
            query: Search keywords

        Returns:
            A list of SearchResult entries
        """
        if not self.api_key:
            logger.error("SerpAPISearch: API key not configured")
            print("Error: SERPAPI_API_KEY not configured. Skipping search.")
            return []

        try:
            # 配置搜索参数
            params = {
                "engine": "google",
                "q": query,
                "api_key": self.api_key,
                "num": 10,  # 返回结果数量
                # 可选: 针对中文搜索优化
                # "gl": "cn",  # 地理位置: 中国
                # "hl": "zh-cn",  # 界面语言: 中文
            }

            logger.info(f"SerpAPISearch: Searching for '{query}'")
            
            # 执行搜索 (同步方法，但在async函数中可以用)
            search = GoogleSearch(params)
            results = search.get_dict()

            # 检查是否有错误
            if 'error' in results:
                error_msg = results['error']
                logger.error(f"SerpAPISearch: API error: {error_msg}")
                print(f"Error: SerpAPI returned error: {error_msg}")
                return []

            # 检查有机搜索结果
            if 'organic_results' not in results:
                logger.warning(f"SerpAPISearch: No organic results found for query: {query}")
                logger.debug(f"Available keys: {list(results.keys())}")
                return []

            organic_results = results['organic_results']
            
            if not organic_results:
                logger.info(f"SerpAPISearch: No results found for query: {query}")
                return []

            # 转换为 SearchResult 格式
            result_list = []
            for item in organic_results:
                try:
                    title = item.get('title', '')
                    link = item.get('link', '')
                    snippet = item.get('snippet', '')
                    position = item.get('position', 0)

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
                                'position': position
                            }],
                            source=f'{title}\n{link}'
                        ))
                except Exception as e:
                    logger.warning(f"SerpAPISearch: Failed to parse result item: {e}")
                    continue

            logger.info(f"SerpAPISearch: Found {len(result_list)} results")
            
            # 记录配额使用情况
            if 'search_metadata' in results:
                total_time = results['search_metadata'].get('total_time_taken', 0)
                logger.info(f"SerpAPISearch: Search completed in {total_time}s")
            
            return result_list

        except ImportError:
            logger.error("SerpAPISearch: google-search-results library not installed")
            print("Error: Please install: pip install google-search-results")
            return []
        except KeyError as e:
            logger.error(f"SerpAPISearch: Unexpected response structure: missing key {e}")
            return []
        except Exception as e:
            logger.error(f"SerpAPISearch: Unexpected error: {type(e).__name__}: {e}")
            print(f"Error: SerpAPISearch failed: {e}")
            return []


# 便捷函数：检查配额使用情况
def check_serpapi_account():
    """检查 SerpAPI 账户信息和配额使用情况"""
    api_key = os.getenv("SERPAPI_API_KEY", "")
    if not api_key:
        print("❌ SERPAPI_API_KEY not configured")
        return
    
    try:
        from serpapi import GoogleSearch
        params = {
            "engine": "google_account",
            "api_key": api_key
        }
        search = GoogleSearch(params)
        account_info = search.get_dict()
        
        print("✅ SerpAPI Account Information:")
        print(f"   Total searches this month: {account_info.get('total_searches_this_month', 'N/A')}")
        print(f"   Plan: {account_info.get('plan', 'N/A')}")
        print(f"   Plan searches left: {account_info.get('plan_searches_left', 'N/A')}")
    except Exception as e:
        print(f"❌ Failed to get account info: {e}")


if __name__ == "__main__":
    # 测试代码
    import asyncio
    
    async def test():
        search_engine = SerpAPISearch()
        results = await search_engine.api_function("浪潮信息 000977")
        
        print(f"\n找到 {len(results)} 条结果:\n")
        for i, result in enumerate(results[:3], 1):
            print(f"{i}. {result.name}")
            print(f"   {result.link}")
            print(f"   {result.description[:100]}...")
            print()
        
        # 检查账户信息
        print("\n检查配额使用情况:")
        check_serpapi_account()
    
    asyncio.run(test())
