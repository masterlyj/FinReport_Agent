"""
Search Engine Implementations

This module aggregates various search engine implementations including:
- Tavily (AI-powered)
- Bing (Requests-based, legacy)
- Bocha (Requests-based, legacy)
- Playwright-based Bing search
- Others (Google Serper, DuckDuckGo, Sogou, etc.)
"""

from typing import List, Optional, Dict, Any
import os
import json
import urllib.parse
import httpx
import asyncio
from bs4 import BeautifulSoup

# Try importing playwright
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

from ..base import Tool, ToolResult
from .base_search import SearchResult, ImageSearchResult
from ...utils.logger import get_logger

logger = get_logger()

# =============================================================================
# Tavily Search (Current Primary)
# =============================================================================

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
            pass # Suppress warning, handled by pool
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
                            data=[{
                                'title': title,
                                'link': link,
                                'snippet': snippet,
                                'score': score,
                                'position': i + 1
                            }],
                            link=link,
                            source=f'{title}\n{link}'
                        ))
                except Exception as e:
                    logger.warning(f"TavilySearch: Failed to parse result item: {e}")
                    continue

            return result_list

        except ImportError:
            logger.error("TavilySearch: 'tavily' package not installed. Please install it.")
            return []
        except Exception as e:
            logger.error(f"TavilySearch: Search failed: {e}")
            return []


# =============================================================================
# Playwright Search (Bing)
# =============================================================================

class PlaywrightSearch(Tool):
    """
    Bing web-search helper implemented with Playwright to support dynamic pages.
    """

    def __init__(self):
        super().__init__(
            name="Bing web search (Playwright)",
            description="Browser-automation Bing search tool that returns result snippets for a query.",
            parameters=[{"name": "query", "type": "str", "description": "Keywords for the search", "required": True}],
        )
        self.backend = 'playwright'
        self.type = 'tool_search'
    
    async def api_function(self, query: str) -> List[ToolResult]:
        """
        Execute a Bing search via Playwright and return structured results.
        """
        if not PLAYWRIGHT_AVAILABLE:
            logger.error("PlaywrightSearch: playwright package not available.")
            return []

        results = []
        async with async_playwright() as p:
            # Launch Chromium
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",
                locale="zh-CN",
                viewport={'width': 2560, 'height': 1440}
            )
            page = await context.new_page()
                
            try:
                # Build the search URL
                search_url = f"https://cn.bing.com/search?q={urllib.parse.quote_plus(query)}"
                
                # Visit the results page
                print(f"Visiting: {search_url}")
                await page.goto(search_url, wait_until="domcontentloaded")
                
                # Handle cookie prompt
                accept_button = page.locator("#bnp_btn_accept")
                try:
                    await accept_button.wait_for(state='visible', timeout=3000)
                    print("Cookie consent detected; accepting...")
                    await accept_button.click()
                except Exception:
                    # print("No cookie prompt detected.")
                    pass

                # Wait for results to load
                # print("Waiting for search results to render...")
                try:
                    await page.locator("#b_results").wait_for(state='visible', timeout=30000)
                except Exception:
                    pass
                # print("Page ready, parsing results...")
                
                # Extract the result list
                result_items = await page.locator("li.b_algo").all()
                # print(f"Found {len(result_items)} results.")

                # Gather result metadata
                for item in result_items:
                    title_element = item.locator("h2 > a")
                    snippet_element = item.locator(".b_caption p")

                    title = await title_element.inner_text() if await title_element.count() > 0 else ""
                    link = await title_element.get_attribute("href") if await title_element.count() > 0 else ""
                    description = await snippet_element.inner_text() if await snippet_element.count() > 0 else ""
                    
                    if title and link:
                        results.append(SearchResult(
                            query=query,
                            name=title,
                            description=description,
                            link=link,
                            data=[{'title': title, 'link': link, 'description': description}],
                            source=f'{title}\n{link}'
                        ))
                        
            except Exception as e:
                logger.error(f"PlaywrightSearch: An error occurred during the search: {e}")
            finally:
                await browser.close()
        
        return results


# =============================================================================
# Legacy / Requests-based Search Engines
# =============================================================================

class BingSearch(Tool):
    """
    Legacy Bing search implementation that relies on HTTP requests with fixed cookies/headers.
    """

    def __init__(self):
        super().__init__(
            name="Bing Web Search (requests)",
            description="HTTP-based Bing search helper for retrieving result summaries.",
            parameters=[{"name": "query", "type": "str", "description": "Search keywords", "required": True}],
        )
 
        self.backend = 'requests'
        self.type = 'tool_search'
        self.headers = {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            "Cookie": "MUID=1C948923B2A965190E139DB3B38764BB; ..."
        }

    async def api_function(self, query: str) -> List[ToolResult]:
        encoded_query = urllib.parse.quote_plus(query)
        url = f"https://cn.bing.com/search?q={encoded_query}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                result_list = []

                # Extract the primary search-result content
                for item in soup.find_all('li', class_='b_algo'):
                    try:
                        title = item.find('h2').text
                        description_tag = item.find('p')
                        description = description_tag.text if description_tag else "No description available"
                        link = item.find('a')['href']
                        result_list.append(SearchResult(
                            query=query,
                            name=title,
                            description=description,
                            link=link,
                            data=[{'title': title, 'description': description, 'link': link}],
                            source=f'{title}\n{link}'
                        ))
                    except Exception as e:
                        logger.warning(f"BingSearch: error extracting result: {e}")

                return result_list
            else:
                logger.error(f"BingSearch: Request failed with status code {response.status_code}")
                return []


class BochaSearch(Tool):
    """
    Legacy Bocha search implementation powered by direct HTTP requests.
    """

    def __init__(self):
        super().__init__(
            name="Bocha web search",
            description="HTTP-based Bocha search helper for retrieving document snippets.",
            parameters=[{"name": "query", "type": "str", "description": "Search keywords", "required": True}],
        )

        self.backend = 'requests'
        self.type = 'tool_search'
        api_key = os.getenv("BOCHAAI_API_KEY", "")
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

    async def api_function(self, query: str) -> List[ToolResult]:
        async with httpx.AsyncClient() as client:
            url = "https://api.bochaai.com/v1/web-search"
            payload = json.dumps({
                "query": query,
                "summary": True,
                "count": 10
            })
            
            response = await client.post(url, headers=self.headers, data=payload)
            try:
                result = response.json()['data']['webPages']['value']
                result_list = []
                if len(result) > 0:
                    for item in result:
                        if 'name' in item and 'url' in item and 'snippet' in item:
                            title = item['name']
                            link = item['url']
                            description = item['summary']
                            result_list.append(SearchResult(
                                query=query,
                                name=title,
                                description=description,
                                link=link,
                                data=[{'title': title, 'link': link, 'description': description}],
                                source=f'{title}\n{link}'
                            ))
                    return result_list
                else:
                    return []
            except Exception as e:
                logger.error(f"BochaSearch: Error parsing response: {e}")
                return []


class SerperSearch(Tool):
    """
    Serper search implementation powered by direct HTTP requests.
    """

    def __init__(self):
        super().__init__(
            name="Google Search Engine",
            description="HTTP-based Google search helper for retrieving document snippets.",
            parameters=[{"name": "query", "type": "str", "description": "Search keywords", "required": True}],
        )

        self.backend = 'requests'
        self.type = 'tool_search'
        api_key = os.getenv("SERPER_API_KEY", "")
        self.headers = {
            'X-API-KEY': api_key,
            'Content-Type': 'application/json'
        }

    async def api_function(self, query: str) -> List[ToolResult]:
        async with httpx.AsyncClient() as client:
            url = "https://google.serper.dev/search"
            payload = json.dumps({
                "q": query,
            })
            
            response = await client.post(url, headers=self.headers, data=payload)
            try:
                result = response.json().get('organic', [])
                result_list = []
                if len(result) > 0:
                    for item in result:
                        title = item.get('title', '')
                        link = item.get('link', '')
                        description = item.get('snippet', '')
                        result_list.append(SearchResult(
                            query=query,
                            name=title,
                            description=description,
                            link=link,
                            data=[{'title': title, 'link': link, 'description': description}],
                            source=f'{title}\n{link}'
                        ))
                    return result_list
                else:
                    return []
            except Exception as e:
                logger.error(f"SerperSearch: Error parsing response: {e}")
                return []


class DuckDuckGoSearch(Tool):
    """
    Legacy DuckDuckGo search implementation based on raw HTTP requests.
    """

    def __init__(self):
        super().__init__(
            name="DuckDuckGo web search (requests)",
            description="DuckDuckGo-powered web search helper that fetches HTML results.",
            parameters=[{"name": "query", "type": "str", "description": "Search keywords", "required": True}],
        )
        self.backend = 'requests'
        self.type = 'tool_search'
        self.headers = {
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }

    async def api_function(self, query: str) -> List[ToolResult]:
        URL = "https://duckduckgo.com/html/"
        params = {'q': query}

        logger.info(f"Searching DuckDuckGo for '{query}'...")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(URL, headers=self.headers, params=params)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'html.parser')
                results_container = soup.find_all('div', class_='result')
                
                if not results_container:
                    return []

                search_results = []
                for result in results_container:
                    title_element = result.find('a', class_='result__a')
                    if not title_element:
                        continue

                    title = title_element.text.strip()
                    raw_link = title_element.get('href', '')
                    
                    # Handle DuckDuckGo redirect links
                    if raw_link and 'uddg=' in raw_link:
                        from urllib.parse import unquote
                        link = unquote(raw_link.split('uddg=')[-1])
                    else:
                        link = raw_link

                    snippet_element = result.find('a', class_='result__snippet')
                    snippet = snippet_element.text.strip() if snippet_element else "..."

                    search_results.append(SearchResult(
                        query=query,
                        name=title,
                        description=snippet,
                        link=link,
                        data=[{'title': title, 'link': link, 'description': snippet}],
                        source=f'{title}\n{link}'
                    ))

                return search_results
        except Exception as e:
            logger.error(f"DuckDuckGoSearch: Error: {e}")
            return []


class SogouSearch(Tool):
    """
    Sogou web search implementation using httpx and BeautifulSoup.
    """

    def __init__(self):
        super().__init__(
            name="Sogou web search",
            description="Search the web using Sogou search engine.",
            parameters=[{"name": "query", "type": "str", "description": "Search keywords", "required": True}],
        )
        self.backend = 'requests'
        self.type = 'tool_search'
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://www.sogou.com/"
        }

    async def api_function(self, query: str) -> List[ToolResult]:
        search_results = []
        try:
            import httpx
            from bs4 import BeautifulSoup
            
            url = "https://www.sogou.com/web"
            params = {"query": query}
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, params=params, headers=self.headers)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    # Sogou results are usually in 'vrwrap' or 'rb' classes
                    results_container = soup.find_all('div', class_=['vrwrap', 'rb'])
                    
                    for result in results_container:
                        title_tag = result.find('h3')
                        if not title_tag:
                            continue
                        
                        a_tag = title_tag.find('a')
                        if not a_tag:
                            continue
                            
                        title = a_tag.get_text(strip=True)
                        link = a_tag.get('href', '')
                        
                        # Sogou links are often redirects
                        if link.startswith('/'):
                            link = "https://www.sogou.com" + link
                            
                        abstract_tag = result.find('div', class_=['vr-abstract', 'str-text-info', 'content-extract'])
                        description = abstract_tag.get_text(strip=True) if abstract_tag else "..."
                        
                        search_results.append(SearchResult(
                            query=query,
                            name=title,
                            description=description,
                            link=link,
                            data=[{'title': title, 'link': link, 'description': description}],
                            source=f'{title}\n{link}'
                        ))
            return search_results
        except Exception as e:
            logger.error(f"SogouSearch: Error: {e}")
            return []


class InDomainSearch_Request(Tool):
    """
    Legacy in-domain financial news search implemented via HTTP requests.
    """

    def __init__(self):
        super().__init__(
            name="Financial site in-domain search (requests)",
            description="Queries pre-selected financial news domains for pages related to the given keywords.",
            parameters=[{"name": "query", "type": "str", "description": "Search keywords", "required": True}],
        )
        self.backend = 'requests'
        self.type = 'tool_search'
        
        self.domain_list = [
            "https://finance.sina.com.cn/",
            "https://china.caixin.com/",
            "https://economy.gmw.cn/",
            "https://www.21jingji.com/",
            "https://www.eeo.com.cn/",
            "https://www.cls.cn/",
            "https://news.hexun.com/"
        ]
        
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Mobile Safari/537.36 EdgA/123.0.0.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br, zsdch, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Referer": "https://www.bing.com/",
        }

    async def api_function(self, query: str) -> List[ToolResult]:
        final_result_list = []
        async with httpx.AsyncClient() as client:
            for domain in self.domain_list[:2]:  # Limit the number of domains per call
                domain_query = f"site:{domain} {query}"
                params = {
                    "q": domain_query, 
                    "sc": "0-10", 
                    "ajaxnorecss": "1", 
                    "jsoncbid": "0", 
                    "qs": "n", 
                    "form": "QBRE", 
                    "sp": "-1"
                }
                url = "https://www.bing.com/search"
                try:
                    response = await client.get(url, headers=self.headers, params=params)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        for item in soup.find_all('li', class_='b_algo'):
                            try:
                                title = item.find('h2').text
                                description_tag = item.find('p')
                                description = description_tag.text if description_tag else "No description available"
                                link = item.find('a')['href']
                                final_result_list.append(SearchResult(
                                    query=query,
                                    name=title,
                                    description=description,
                                    link=link,
                                    data=[{'title': title, 'description': description, 'link': link}],
                                    source=f'{title}\n{link}'
                                ))
                            except Exception:
                                continue
                except Exception as e:
                    logger.error(f"InDomainSearch_Request: Error searching domain {domain}: {e}")
        return final_result_list


class BingImageSearch(Tool):
    """
    Legacy Bing image search helper built on direct HTTP requests.
    """

    def __init__(self):
        super().__init__(
            name="Bing image search",
            description="Image search helper that scrapes Bing image results for a query.",
            parameters=[
                {"name": "query", "type": "str", "description": "Keywords for the image search", "required": True}
            ],
        )
        self.backend = 'requests'
        self.type = 'tool_search'

        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
            "Connection": "keep-alive",
        }

    async def api_function(self, query: str) -> List[ToolResult]:
        # Build the image-search URL
        url = f"https://www.bing.com/images/search?q={query}&form=HDRSC3&first=1"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url=url, headers=self.headers, timeout=10)
                response.raise_for_status()

                # Parse the HTML payload
                soup = BeautifulSoup(response.text, 'html.parser')
                result_list = []

                # Locate image metadata
                image_items = soup.find_all('a', class_='iusc')

                for item in image_items:
                    try:
                        # Parse the embedded JSON metadata
                        json_data = json.loads(item['m'])
                        
                        # Extract fields
                        title = json_data.get('t', "Untitled")
                        image_url = json_data.get('murl')
                        page_url = json_data.get('purl')

                        if image_url and page_url:
                            result_list.append(ImageSearchResult(
                                query=query,
                                name=title,
                                description=f"Image search result: {title}",
                                link=page_url,
                                data=[{
                                    'title': title,
                                    'image_url': image_url,
                                    'page_url': page_url
                                }]
                            ))
                    except (KeyError, json.JSONDecodeError, TypeError):
                        continue

                if not result_list:
                    return []

                return result_list
        except httpx.RequestError as e:
            logger.error(f"BingImageSearch: Error: {e}")
            return []
