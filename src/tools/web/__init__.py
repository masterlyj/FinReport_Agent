"""
Web Search and Crawler Tools Module

This module provides comprehensive web search capabilities including:
- Multi-engine parallel search with intelligent quota management
- Web content crawling and extraction
- Unified search result interfaces
"""

from .base_search import SearchResult, ImageSearchResult
from .quota_manager import QuotaManager
from .search_engine_pool import SearchEnginePool, SearchStrategy, create_default_pool
from .search_engine_serpapi import SerpAPISearch
from .search_engine_requests import (
    SerperSearch,
    BingSearch,
    DuckDuckGoSearch,
    SogouSearch,
    BochaSearch,
    InDomainSearch_Request,
    BingImageSearch
)
from .web_crawler import Click, ClickResult

__all__ = [
    # Base classes
    "SearchResult",
    "ImageSearchResult",
    
    # Quota management
    "QuotaManager",
    
    # Search engine pool
    "SearchEnginePool",
    "SearchStrategy",
    "create_default_pool",
    
    # Search engines
    "SerpAPISearch",
    "SerperSearch",
    "BingSearch",
    "DuckDuckGoSearch",
    "SogouSearch",
    "BochaSearch",
    "InDomainSearch_Request",
    "BingImageSearch",
    
    # Crawler
    "Click",
    "ClickResult",
]

