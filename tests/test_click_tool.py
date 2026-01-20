import asyncio
import os
import sys
import warnings

# 忽略 ResourceWarning 和 DeprecationWarning
warnings.filterwarnings("ignore", category=ResourceWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools.web.web_crawler import Click
from src.config import Config

async def _run_click_check():
    print("Initializing Click tool...")
    click_tool = Click()
    
    # 测试一个简单的 URL
    test_url = "https://www.baidu.com"
    print(f"Testing Click tool with URL: {test_url}")
    
    try:
        results = await click_tool.api_function(url=test_url)
        
        if results and len(results) > 0:
            result = results[0]
            print("\n--- Click Result Success ---")
            print(f"Name: {result.name}")
            print(f"Link: {result.link}")
            print(f"Content length: {len(result.content)} characters")
            print(f"Content preview: {result.content[:200]}...")
            print("----------------------------\n")
            return True
        else:
            print("Click tool returned no results.")
            return False
            
    except Exception as e:
        print(f"Click tool test failed with error: {e}")
        return False

if __name__ == "__main__":
    try:
        asyncio.run(_run_click_check())
    except Exception as e:
        print(f"Unhandled error: {e}")
    finally:
        # 给异步循环一点时间来清理资源
        import time
        time.sleep(1)

