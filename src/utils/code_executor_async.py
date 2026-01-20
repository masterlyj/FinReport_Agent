import asyncio
import io
import sys
import os
import dill  # 使用dill代替pickle, 更强的序列化能力
import traceback
import uuid
import inspect
import importlib
import types
from contextlib import redirect_stdout, redirect_stderr
from typing import Dict, Any, List, Tuple
import pandas as pd

class AsyncCodeExecutor:
    """
    轻量级Python沙箱，可用于异步执行LLM生成的代码。
    """
    def __init__(self, working_dir: str):
        self.working_dir = working_dir
        os.makedirs(self.working_dir, exist_ok=True)
        self.session_id = str(uuid.uuid4())
        self.globals: Dict[str, Any] = self.create_clean_globals()

    def create_clean_globals(self) -> Dict[str, Any]:
        """
        创建包含常用内建和预导入库的全局命名空间。
        """
        context = {'__builtins__': __builtins__}

        import os
        import json
        import math
        import re
        import random
        import datetime
        import asyncio
        import io
        import sys
        
        context.update({
            'os': os,
            'json': json,
            'math': math,
            're': re,
            'random': random,
            'datetime': datetime,
            'asyncio': asyncio,
            'io': io,
            'sys': sys
        })

        try:
            import pandas as pd
            import numpy as np
            import matplotlib
            matplotlib.use('Agg')  # Force non-interactive backend
            import matplotlib.pyplot as plt
            import matplotlib.font_manager as fm
            # 字体设置与可视化环境兼容配置（已注释字体文件部分，若有需要可按需放开）
            # font_path = os.path.join(os.path.dirname(__file__), 'fonts', 'kt_font.ttf')
            # if os.path.exists(font_path):
            #     fm.fontManager.addfont(font_path)
            #     font_prop = fm.FontProperties(fname=font_path)
            #     custom_font_name = font_prop.get_name()
            #     matplotlib.rcParams['font.family'] = custom_font_name
            #     matplotlib.rcParams['font.sans-serif'] = [custom_font_name, 'SimHei', 'Arial Unicode MS']
            # else:
            matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'sans-serif']
            matplotlib.rcParams['axes.unicode_minus'] = False
            context.update({
                'pd': pd,
                'pandas': pd,
                'np': np,
                'numpy': np,
                'plt': plt,
                'matplotlib': matplotlib,
            })
        except ImportError as e:
            print(f"警告：无法预导入数据分析相关库: {e}")

        return context


    def set_variable(self, name: str, value: Any):
        """
        向执行器全局作用域注入外部变量或函数。
        """
        self.globals[name] = value

    def get_variable(self, name: str) -> Any:
        """
        从执行器全局作用域获取变量。
        """
        return self.globals.get(name)

    def save_state(self) -> bytes:
        """
        保存最简但可还原的运行状态：
        - imports: 恢复时需要导入的模块名
        - definitions: 用户自定义函数/类的源码
        - variables: 简单可序列化变量（复杂对象尽量跳过）
        """
        state: Dict[str, Any] = {
            'imports': [],
            'definitions': [],  # 存储结构: {'name', 'kind', 'source'}
            'variables': {},    # 名字 -> dill序列化bytes
        }

        # 1) 记录所有已导入模块
        module_names: List[str] = []
        for name, value in list(self.globals.items()):
            if isinstance(value, types.ModuleType):
                if value.__name__ not in ('__builtins__',):
                    module_names.append(value.__name__)
        # 去重并排序，保证一致性
        state['imports'] = sorted(set(module_names))

        # 2) 收集所有用户自定义的函数/类定义（附源码）
        def try_collect_definition(obj_name: str, obj: Any, kind: str):
            try:
                # 仅采集通过exec方式定义的对象（<string> 或 __main__）
                source = inspect.getsource(obj)
                state['definitions'].append({'name': obj_name, 'kind': kind, 'source': source})
            except Exception:
                # 源码获取失败时跳过
                pass

        for name, value in list(self.globals.items()):
            # 跳过特殊名字
            if name.startswith('__') and name.endswith('__'):
                continue
            if inspect.isfunction(value):
                try_collect_definition(name, value, 'function')
            elif inspect.isclass(value):
                try_collect_definition(name, value, 'class')

        # 3) 保存简单变量/对象（尽量用dill序列化）
        SIMPLE_ALLOWED_TYPES = (int, float, str, bool)
        CONTAINER_TYPES = (list, dict, tuple, set)

        def is_simple(obj: Any, depth: int = 0) -> bool:
            """
            判断对象是否结构简单（递归，简单类型或简单容器），便于序列化
            """
            if isinstance(obj, SIMPLE_ALLOWED_TYPES):
                return True
            if isinstance(obj, (pd.DataFrame, )):
                return False
            if isinstance(obj, CONTAINER_TYPES) and depth < 2:
                try:
                    if isinstance(obj, dict):
                        return all(isinstance(k, (str, int)) and is_simple(v, depth + 1) for k, v in obj.items())
                    else:
                        return all(is_simple(v, depth + 1) for v in obj)
                except Exception:
                    return False
            return False

        for name, value in list(self.globals.items()):
            if name in ('__builtins__',):
                continue
            if inspect.isfunction(value) or inspect.isclass(value) or isinstance(value, types.ModuleType):
                continue
            if name.startswith('_'):
                continue
            # 优先保存简单变量，复杂对象只做尝试
            to_store = None
            if is_simple(value):
                try:
                    to_store = dill.dumps(value)
                except Exception:
                    to_store = None
            else:
                # 复杂对象：dill序列化失败时跳过
                try:
                    to_store = dill.dumps(value)
                except Exception:
                    to_store = None
            if to_store is not None:
                state['variables'][name] = to_store

        try:
            return dill.dumps(state)
        except Exception as e:
            print(f"[{self.session_id}] 警告：保存沙箱轻量状态失败: {e}")
            return dill.dumps({'imports': [], 'definitions': [], 'variables': {}})

    def load_state(self, state: bytes):
        """
        恢复轻量级状态：重新导入模块，还原函数/类定义，还原变量。
        """
        try:
            payload = dill.loads(state)
        except Exception as e:
            print(f"[{self.session_id}] 错误：沙箱状态加载失败: {e}。环境已重置为空。")
            self.globals = self.create_clean_globals()
            return

        self.globals = self.create_clean_globals()

        # 1) 重新导入所有需要的模块
        for mod_name in payload.get('imports', []) or []:
            try:
                mod = importlib.import_module(mod_name)
                self.globals[mod_name.split('.')[-1]] = mod
            except Exception:
                # 导入失败模块跳过
                continue

        # 2) 还原所有函数/类定义
        for item in payload.get('definitions', []) or []:
            source = item.get('source')
            if not source:
                continue
            try:
                exec(source, self.globals)
            except Exception:
                # 依赖丢失的函数/类定义跳过
                continue

        # 3) 还原所有普通变量
        for name, raw in (payload.get('variables', {}) or {}).items():
            try:
                self.globals[name] = dill.loads(raw)
            except Exception:
                # 反序列化失败时跳过
                continue
    

    def get_environment_info(self) -> str:
        """
        总结当前沙箱环境主要变量，可用于构造辅助提示。
        """
        info_parts = []
        
        # 收集所有重要的数据变量
        important_vars = {}
        for var_name, var_value in self.globals.items():
            if not var_name.startswith('_') and var_name not in ['In', 'Out', 'get_ipython', 'exit', 'quit']:
                try:
                    if hasattr(var_value, 'shape'):  # 主要针对pandas的DataFrame/numpy数组
                        important_vars[var_name] = f"{type(var_value).__name__}，shape为{var_value.shape}"
                    elif var_name in ['session_output_dir']:  # 关键路径变量
                        important_vars[var_name] = str(var_value)
                    elif isinstance(var_value, (int, float, str, bool)) and len(str(var_value)) < 100:
                        important_vars[var_name] = f"{type(var_value).__name__}: {var_value}"
                    elif hasattr(var_value, '__module__') and var_value.__module__ in ['pandas', 'numpy', 'matplotlib.pyplot']:
                        important_vars[var_name] = f"已导入模块: {var_value.__module__}"
                    if isinstance(var_value, pd.DataFrame):
                        # 附带DataFrame的dtypes信息
                        important_vars[var_name] += f"，字段类型: {str(var_value.dtypes)}"
                except:
                    continue
        
        if important_vars:
            info_parts.append("当前环境重要变量：")
            for var_name, var_info in important_vars.items():
                info_parts.append(f"- {var_name}: {var_info}")
        else:
            info_parts.append("环境已预加载 pandas、numpy、matplotlib 等常用库。")
        
        if 'session_output_dir' in self.globals:
            info_parts.append(f"图片输出目录：session_output_dir = '{self.globals['session_output_dir']}'")
        
        return "\n".join(info_parts)

    async def execute(self, code: str) -> dict:
        """
        异步执行Python代码，底层通过线程池防阻塞事件循环。
        若用户代码定义`async def async_main():`，则首次exec后自动await执行以支持异步能力。

        返回: {stdout: str, stderr: str, error: bool}
        """
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        has_error = False
        header = "import matplotlib.pyplot as plt; plt.rcParams['font.sans-serif'] = ['SimHei']; plt.rcParams['axes.unicode_minus'] = False"       
        code = header + '\n' + code
        # 使用线程池封装同步exec，避免阻塞主事件循环
        def sync_exec():
            nonlocal has_error
            try:
                # 重定向标准输出/错误
                with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                    # 以自定义全局变量运行用户代码
                    exec(code, self.globals)
            except Exception:
                # 捕获出错信息
                has_error = True
                stderr_capture.write(traceback.format_exc())
                print("代码运行异常，当前代码为：\n", code)

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, sync_exec)
        
        # 如有用户自定义async_main异步入口则接着await运行
        if 'async_main' in self.globals and \
           asyncio.iscoroutinefunction(self.globals['async_main']):
            
            try:
                # 跟同步部分一样重定向输出
                with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                    # 执行异步入口
                    await self.globals['async_main']()
            except Exception:
                has_error = True
                stderr_capture.write(traceback.format_exc())
            finally:
                # 清理，避免重复运行
                del self.globals['async_main']
        
        stdout = stdout_capture.getvalue()
        stderr = stderr_capture.getvalue()
        if stdout == "":
            stdout = '运行完成，无输出。'
        return {
            'stdout': stdout,
            'stderr': stderr,
            'error': has_error
        }

