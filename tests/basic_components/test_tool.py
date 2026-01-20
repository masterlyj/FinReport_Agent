import argparse
import os
import sys
from pathlib import Path

root = str(Path(__file__).resolve().parents[2])
sys.path.append(root)
import asyncio
from src.tools import (
    get_avail_tools, 
    get_tool_by_name, 
    get_tool_categories, 
    list_tools, 
    get_tool_info,
)
from dotenv import load_dotenv
load_dotenv()

if __name__ == "__main__":

    # all_tools = get_tool_categories() # 获取所有类别的工具名
    all_tools = list_tools() # 获取所有工具名列表
    print(f"Available tools: {all_tools}")

    # tool = get_tool_by_name('Bocha web search')()
    tool_cls = get_tool_by_name('Click')
    if tool_cls:
        tool = tool_cls()
        print(f"Testing tool: {tool.name}")
        result = asyncio.run(tool.api_function('https://www.baidu.com'))
        print(result)
    else:
        print("Tool 'Click' not found.")

