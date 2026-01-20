import argparse
import os
import sys
from pathlib import Path
import asyncio

root = str(Path(__file__).resolve().parents[2])
sys.path.append(root)

from src.config import Config
from src.utils import AsyncCodeExecutor

async def main():
    print("\n--- [Test 1: Basic Execution & Package Import] ---")
    executor_1 = AsyncCodeExecutor(working_dir=".cache")
    
    executor_1.set_variable("my_message", "Hello, World!")
    
    # 1. 测试错误捕获机制 (Test Error Handling)
    print("\n[Case 1] Testing Error Handling (Expected: NameError)")
    code_string_error = """
import pandas as pd
a = 42
b = 329
print(a + b)
print(xxx)  # Intentionally undefined variable
"""
    result_error = await executor_1.execute(code_string_error)
    if result_error['error'] and "NameError" in result_error['stderr']:
        print(f"✅ Successfully caught expected error:\n   {result_error['stderr'].strip().splitlines()[-1]}")
    else:
        print(f"❌ Failed to catch expected error. Result: {result_error}")

    print("\n" + "-"*30)

    # 2. 测试正常代码执行 (Test Normal Execution)
    print("\n[Case 2] Testing Normal Execution")
    code_string_normal = """
a = 100
b = 200
print(f"Sum is: {a+b}")
"""
    result_normal = await executor_1.execute(code_string_normal)
    if not result_normal['error'] and "Sum is: 300" in result_normal['stdout']:
        print(f"✅ Code executed successfully. Output: {result_normal['stdout'].strip()}")
    else:
        print(f"❌ Execution failed: {result_normal}")

    print("\n" + "-"*30)

    # 3. 测试变量注入与状态保持 (Test Variable Injection)
    print("\n[Case 3] Testing Variable Injection")
    result_var = await executor_1.execute("print(my_message)")
    if "Hello, World!" in result_var['stdout']:
         print(f"✅ Variable injected successfully: {result_var['stdout'].strip()}")
    else:
         print(f"❌ Variable injection failed: {result_var}")

    print("\n" + "-"*30)

    # 4. 测试函数传递 (Test Function Injection)
    # 注意：函数中修改外部不可变变量需要 global 声明，这里演示正确的函数调用
    print("\n[Case 4] Testing Function Injection")
    
    def test_function(x):
        return f"Function called with {x}, result={x+1}"
        
    executor_1.set_variable("test_function", test_function)
    result_func = await executor_1.execute("print(test_function(10))")
    
    if "result=11" in result_func['stdout']:
        print(f"✅ Function execution success: {result_func['stdout'].strip()}")
    else:
        print(f"❌ Function execution failed: {result_func}")

if __name__ == "__main__":
    asyncio.run(main())