import asyncio
import httpx
from typing import List, Dict, Any, Optional
from pydantic import Field
from .base_search import SearchResult
from ..base import Tool, ToolResult
from ...utils.logger import get_logger

logger = get_logger()

class ClickResult(SearchResult):
    """Result of a web crawling action."""
    content: str = Field("", description="Extracted markdown content from the page")
    
    def __str__(self):
        return f"Click Result for {self.link}\nTitle: {self.name}\nContent Preview: {self.content[:200]}..."

class Click(Tool):
    """
    Tool for crawling web pages and extracting content.
    Uses crawl4ai as primary engine with fallback to simple fetch.
    """

    def __init__(self):
        super().__init__(
            name="Click",
            description="Extract full content from a given URL. Useful for reading specific articles or reports.",
            parameters=[{
                "name": "url",
                "type": "str",
                "description": "The URL to crawl",
                "required": True
            }]
        )
        self.backend = 'crawl4ai'
        self.type = 'tool_crawler'

    async def fetch_url(self, url: str) -> str:
        """Fallback method to fetch URL content using httpx."""
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                # Simple markdown-like conversion or just return text
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                return soup.get_text(separator='\n', strip=True)
        except Exception as e:
            logger.error(f"Fallback fetch failed for {url}: {e}")
            return f"Error fetching content: {str(e)}"

    async def api_function(self, url: str) -> List[ClickResult]:
        """Execute the crawling action."""
        content = ""
        success = False
        
        try:
            from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
            
            browser_conf = BrowserConfig(headless=True, verbose=False)
            run_conf = CrawlerRunConfig(cache_mode="BYPASS")
            
            async with AsyncWebCrawler(config=browser_conf) as crawler:
                result = await crawler.arun(url=url, config=run_conf)
                if result and result.success:
                    content = result.markdown
                    success = True
                else:
                    logger.warning(f"Crawl4AI failed for {url}, falling back...")
        except Exception as e:
            logger.warning(f"Crawl4AI error for {url}: {e}, falling back...")

        if not success:
            content = await self.fetch_url(url)
            
        return [ClickResult(
            name="Web Page Content",
            description=f"Extracted content from {url}",
            data={"content": content},
            link=url,
            content=content,
            source=f"Crawled from {url}"
        )]
