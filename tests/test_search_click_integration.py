import asyncio
import os
import sys
import warnings
import time
from typing import List

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools.web.search_engines import SogouSearch, BingSearch
from src.tools.web.web_crawler import Click
from src.tools.web.base_search import SearchResult

# Ignore warnings
warnings.filterwarnings("ignore", category=ResourceWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

async def _run_engine_test(engine_name: str, engine_instance, click_tool, query: str):
    print(f"\n{'='*20} Testing {engine_name} {'='*20}")
    print(f"Query: {query}")
    
    # 1. Search
    print(f"\n[Step 1] Searching with {engine_name}...")
    try:
        results: List[SearchResult] = await engine_instance.api_function(query=query)
        if not results:
            print(f"[FAIL] {engine_name} returned NO results.")
            return False
        
        print(f"[PASS] {engine_name} returned {len(results)} results.")
        first_result = results[0]
        print(f"   First Result: {first_result.name}")
        print(f"   URL: {first_result.link}")
        
        # 2. Click (Crawl)
        target_url = first_result.link
        if not target_url.startswith("http"):
             print(f"[FAIL] Invalid URL format: {target_url}")
             return False

        print(f"\n[Step 2] Crawling URL with Click tool...")
        crawl_results = await click_tool.api_function(url=target_url)
        
        if crawl_results and len(crawl_results) > 0:
            content = crawl_results[0].content
            if len(content) > 100:
                print(f"[PASS] Crawl SUCCESS. Content length: {len(content)} chars")
                try:
                    print(f"   Preview: {content[:100].replace(chr(10), ' ')}...")
                except:
                    print("   Preview: (content cannot be printed)")
                return True
            else:
                print(f"[WARN] Crawl returned very short content ({len(content)} chars). Might be blocked or empty.")
                return True # Still technically successful execution
        else:
            print("[FAIL] Click tool returned no results.")
            return False

    except Exception as e:
        print(f"[FAIL] Error during {engine_name} test: {e}")
        # import traceback
        # traceback.print_exc()
        return False

async def main():
    # Initialize tools
    sogou = SogouSearch()
    bing = BingSearch()
    click = Click()
    
    query = "DeepSeek LLM latest news"
    
    # Test Sogou
    # Note: Sogou might fail due to anti-spider, we print result but continue
    sogou_success = await _run_engine_test("SogouSearch", sogou, click, query)
    
    # Test Bing
    time.sleep(2)
    bing_success = await _run_engine_test("BingSearch", bing, click, query)
    
    print(f"\n{'='*20} Summary {'='*20}")
    print(f"Sogou + Click: {'[PASS]' if sogou_success else '[FAIL] (Expected if anti-spider is active)'}")
    print(f"Bing + Click:  {'[PASS]' if bing_success else '[FAIL]'}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTest interrupted.")
    except Exception as e:
        print(f"\nUnhandled exception: {e}")
    finally:
        time.sleep(1)
