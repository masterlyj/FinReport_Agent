"""
搜索引擎池管理器

负责智能管理多个搜索引擎，支持：
- 并发查询多个引擎
- 自动配额管理和降级
- 结果去重和合并
"""

import asyncio
from typing import List, Dict, Set, Optional
from dataclasses import dataclass
from .quota_manager import QuotaManager
from .base_search import SearchResult
from ...utils.logger import get_logger

logger = get_logger()


@dataclass
class SearchStrategy:
    """搜索策略配置"""
    name: str
    engines: List[str]  # 引擎名称列表
    parallel: bool = True  # 是否并发执行
    description: str = ""


class SearchEnginePool:
    """
    搜索引擎池：智能管理多引擎并发查询
    
    支持多种查询策略和自动降级
    """
    
    # 预定义策略
    STRATEGIES = {
        "premium": SearchStrategy(
            name="premium",
            engines=["serpapi", "duckduckgo"],
            parallel=True,
            description="SerpAPI(付费高质量) + DuckDuckGo(免费备用) 并发查询"
        ),
        "fallback": SearchStrategy(
            name="fallback",
            engines=["tavily", "duckduckgo"],
            parallel=True,
            description="Tavily(付费AI搜索) + DuckDuckGo(免费) 并发查询"
        ),
        "free_only": SearchStrategy(
            name="free_only",
            engines=["duckduckgo"],
            parallel=False,
            description="仅使用DuckDuckGo免费搜索"
        ),
        "best_effort": SearchStrategy(
            name="best_effort",
            engines=["serpapi", "tavily", "duckduckgo"],
            parallel=True,
            description="所有可用引擎并发，尽力而为"
        )
    }
    
    def __init__(self, engines: Dict, quota_manager: Optional[QuotaManager] = None):
        """
        初始化搜索引擎池
        
        Args:
            engines: Dict[str, Tool] - 引擎实例字典
                例如: {
                    "serpapi": SerpAPISearch(),
                    "duckduckgo": DuckDuckGoSearch(),
                    "tavily": TavilySearch()
                }
            quota_manager: 配额管理器实例，None则自动创建
        """
        self.engines = engines
        self.quota_manager = quota_manager or QuotaManager()
        
        logger.info(f"SearchEnginePool initialized with {len(engines)} engines: {list(engines.keys())}")
    
    async def search(
        self,
        query: str,
        max_results: int = 10,
        strategy: str = "auto",
        timeout: float = 30.0
    ) -> List[SearchResult]:
        """
        智能多引擎搜索
        
        Args:
            query: 搜索关键词
            max_results: 最大返回结果数
            strategy: 策略名称 ("auto", "premium", "fallback", "free_only", "best_effort")
            timeout: 搜索超时时间（秒）
        
        Returns:
            去重合并后的搜索结果列表
        """
        logger.info(f"Starting search for query: '{query}' with strategy: {strategy}")
        
        # 自动选择策略
        if strategy == "auto":
            strategy = self._select_strategy()
            logger.info(f"Auto-selected strategy: {strategy}")
        
        if strategy not in self.STRATEGIES:
            logger.warning(f"Unknown strategy '{strategy}', falling back to 'free_only'")
            strategy = "free_only"
        
        search_strategy = self.STRATEGIES[strategy]
        logger.info(f"Strategy: {search_strategy.description}")
        
        # 过滤可用引擎
        available_engines = self._filter_available_engines(search_strategy.engines)
        
        if not available_engines:
            logger.error("No available search engines! All quotas exhausted or engines not configured.")
            return []
        
        logger.info(f"Available engines: {available_engines}")
        
        # 执行搜索（带超时）
        try:
            if search_strategy.parallel and len(available_engines) > 1:
                results_list = await asyncio.wait_for(
                    self._parallel_search(query, available_engines),
                    timeout=timeout
                )
            else:
                results_list = await asyncio.wait_for(
                    self._sequential_search(query, available_engines),
                    timeout=timeout
                )
        except asyncio.TimeoutError:
            logger.error(f"Search timeout after {timeout}s")
            return []
        
        # 合并去重
        merged_results = self._merge_and_deduplicate(results_list)
        
        # 限制结果数量
        final_results = merged_results[:max_results]
        
        logger.info(f"Search completed: {len(final_results)} unique results from {len(available_engines)} engines")
        
        return final_results
    
    def _select_strategy(self) -> str:
        """
        自动选择最佳策略
        
        优先级:
        1. premium (SerpAPI有额度)
        2. fallback (Tavily有额度)
        3. free_only (最后备选)
        """
        # 优先使用premium（SerpAPI质量最高）
        if self.quota_manager.check_quota("serpapi") and "serpapi" in self.engines:
            return "premium"
        
        # SerpAPI配额用尽，尝试Tavily
        if self.quota_manager.check_quota("tavily") and "tavily" in self.engines:
            return "fallback"
        
        # 所有付费配额用尽，使用免费
        logger.info("All paid quotas exhausted, using free_only strategy")
        return "free_only"
    
    def _filter_available_engines(self, engine_names: List[str]) -> List[str]:
        """
        过滤可用的搜索引擎
        
        检查条件：
        1. 引擎已注册（在self.engines中）
        2. 有配额可用
        3. API Key已配置（通过检查环境变量）
        """
        available = []
        
        for engine_name in engine_names:
            # 检查是否注册
            if engine_name not in self.engines:
                logger.debug(f"Engine '{engine_name}' not registered, skipping")
                continue
            
            # 检查配额
            if not self.quota_manager.check_quota(engine_name):
                logger.info(f"Engine '{engine_name}' quota exhausted, skipping")
                continue
            
            # 检查API Key（通过engine的api_key属性）
            engine = self.engines[engine_name]
            if hasattr(engine, 'api_key') and not engine.api_key:
                logger.debug(f"Engine '{engine_name}' API key not configured, skipping")
                continue
            
            available.append(engine_name)
        
        return available
    
    async def _parallel_search(
        self,
        query: str,
        engine_names: List[str]
    ) -> List[List[SearchResult]]:
        """
        并发搜索多个引擎
        
        使用 asyncio.gather 实现真正的并发
        """
        logger.info(f"Starting parallel search with {len(engine_names)} engines")
        
        tasks = []
        for engine_name in engine_names:
            engine = self.engines[engine_name]
            task = asyncio.create_task(
                self._safe_search(engine, engine_name, query),
                name=f"search_{engine_name}"
            )
            tasks.append(task)
        
        # 并发执行，收集所有结果（包括异常）
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 过滤异常结果
        valid_results = []
        for i, result in enumerate(results):
            engine_name = engine_names[i]
            if isinstance(result, Exception):
                logger.error(f"Engine '{engine_name}' failed with exception: {result}")
            elif result:
                logger.debug(f"Engine '{engine_name}' returned {len(result)} results")
                valid_results.append(result)
            else:
                logger.debug(f"Engine '{engine_name}' returned no results")
        
        return valid_results
    
    async def _sequential_search(
        self,
        query: str,
        engine_names: List[str]
    ) -> List[List[SearchResult]]:
        """
        顺序搜索（备用策略，单引擎或降级时使用）
        """
        logger.info(f"Starting sequential search with {len(engine_names)} engines")
        
        results = []
        for engine_name in engine_names:
            engine = self.engines[engine_name]
            try:
                result = await self._safe_search(engine, engine_name, query)
                if result:
                    results.append(result)
            except Exception as e:
                logger.error(f"Engine '{engine_name}' failed: {e}")
        
        return results
    
    async def _safe_search(
        self,
        engine,
        engine_name: str,
        query: str
    ) -> List[SearchResult]:
        """
        安全执行搜索（带配额记录和错误处理）
        
        Returns:
            搜索结果列表，失败返回空列表
        """
        try:
            logger.debug(f"Calling {engine_name}.api_function('{query}')")
            
            # 调用引擎的api_function
            results = await engine.api_function(query)
            
            # 记录配额使用（仅在成功获取结果时）
            if results and len(results) > 0:
                self.quota_manager.use_quota(engine_name, count=1)
                remaining = self.quota_manager.get_remaining(engine_name)
                logger.info(
                    f"✓ {engine_name}: {len(results)} results, "
                    f"quota remaining: {remaining if remaining != -1 else 'Unlimited'}"
                )
            else:
                logger.info(f"✗ {engine_name}: No results")
            
            return results or []
            
        except Exception as e:
            logger.error(f"✗ {engine_name} search failed: {type(e).__name__}: {e}")
            return []
    
    def _merge_and_deduplicate(
        self,
        results_list: List[List[SearchResult]]
    ) -> List[SearchResult]:
        """
        合并和去重搜索结果
        
        去重策略：
        1. 基于URL去重（忽略大小写和尾部斜杠）
        2. 保持第一个出现的结果（优先保留高质量引擎的结果）
        
        Args:
            results_list: 多个引擎的结果列表
        
        Returns:
            去重合并后的结果
        """
        seen_urls: Set[str] = set()
        merged_results = []
        
        total_before = sum(len(results) for results in results_list)
        
        # 按引擎顺序合并（第一个引擎的结果优先）
        for results in results_list:
            for result in results:
                # 标准化URL用于去重
                url = result.link.lower().strip().rstrip('/')
                
                # 去重
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    merged_results.append(result)
        
        duplicates = total_before - len(merged_results)
        if duplicates > 0:
            logger.info(f"Removed {duplicates} duplicate results")
        
        logger.debug(f"Merged {len(merged_results)} unique results from {total_before} total")
        
        return merged_results
    
    def get_quota_status(self) -> Dict:
        """获取所有引擎的配额状态"""
        return self.quota_manager.get_status()
    
    def print_quota_status(self):
        """打印配额状态（便捷方法）"""
        print(self.quota_manager)


# 便捷函数：创建默认搜索引擎池
def create_default_pool():
    """
    创建默认的搜索引擎池（包含所有可用引擎）
    
    Returns:
        SearchEnginePool实例
    """
    from .search_engine_serpapi import SerpAPISearch
    from .search_engine_requests import DuckDuckGoSearch
    # from .search_engine_tavily import TavilySearch  # 如果实现了
    
    engines = {
        "serpapi": SerpAPISearch(),
        "duckduckgo": DuckDuckGoSearch(),
        # "tavily": TavilySearch(),
    }
    
    return SearchEnginePool(engines)


if __name__ == "__main__":
    # 测试代码
    import asyncio
    
    async def test():
        print("=== SearchEnginePool Test ===\n")
        
        pool = create_default_pool()
        
        # 查看配额状态
        print("Initial quota status:")
        pool.print_quota_status()
        print()
        
        # 测试搜索
        print("Testing search with auto strategy...")
        results = await pool.search("Python asyncio tutorial", max_results=5)
        
        print(f"\nFound {len(results)} results:\n")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result.name}")
            print(f"   {result.link}")
            print()
        
        # 查看更新后的配额
        print("Quota status after search:")
        pool.print_quota_status()
    
    asyncio.run(test())
