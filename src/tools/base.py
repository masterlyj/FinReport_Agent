import pandas as pd
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict, model_validator
from ..utils.retry import async_retry, async_safe_execute
from ..utils.logger import get_logger

logger = get_logger()

class Tool:
    """
    工具基类，提供统一的工具接口和错误处理

    所有工具都应该继承此类并实现 api_function 方法
    """
    def __init__(
        self,
        name: str,
        description: str,
        parameters: List[Dict[str, Any]],
        max_retries: int = 3
    ):
        self.name = name
        self.type = f'tool_{name}'
        self.id = f"tool_{name}_{uuid.uuid4().hex[:8]}"
        self.short_description = description
        self.parameters = parameters
        self.max_retries = max_retries

    def prepare_params(self, task) -> dict:
        """
        Optional hook to derive API parameters from a task payload.
        """
        return {}
    
    @property
    def description(self):
        params_str = ", ".join([
            f"{p['name']}: {p['type']} ({p['description']})"
                for p in self.parameters
        ])
        return f"Tool name: {self.name}\nDescription: {self.short_description}\nParameters: {params_str}\n"

    async def api_function(self, **kwargs):
        """
        Execute the underlying API and return structured data.
        """
        raise NotImplementedError

    async def get_data(self, task):
        """
        获取数据的主方法，带错误处理和重试机制

        Args:
            task: 任务对象

        Returns:
            获取到的数据列表
        """
        params = self.prepare_params(task)

        try:
            # 使用重试机制调用 API
            data = await self._get_data_with_retry(**params)

            if data and hasattr(task, 'all_results'):
                task.all_results.extend(data)

            logger.info(f"工具 {self.name} 成功获取数据，数量: {len(data) if data else 0}")
            return data

        except Exception as e:
            logger.error(f"工具 {self.name} 获取数据失败: {str(e)}", extra={"tool": self.name, "error": str(e)})
            return []

    async def _get_data_with_retry(self, **params):
        """内部方法：带重试的数据获取"""
        # 动态创建带重试的函数
        @async_retry(max_attempts=self.max_retries, delay=1.0, backoff=2.0)
        async def _fetch():
            return await self.api_function(**params)

        return await _fetch()


class ToolResult(BaseModel):
    """
    工具执行结果的封装类 (Pydantic Model)
    
    提供统一的数据访问接口和格式化输出
    """
    name: str = Field(..., description="Tool/Data name")
    description: str = Field(..., description="Description of the result")
    data: Any = Field(..., description="The actual data payload")
    source: str = Field("", description="Source of the data")
    
    # 允许任意类型（如 pandas DataFrame）
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @model_validator(mode='before')
    @classmethod
    def unpack_single_element_list(cls, data: Any) -> Any:
        # 从原始类中自动解包单元素列表的逻辑
        if isinstance(data, dict) and 'data' in data and isinstance(data['data'], list) and len(data['data']) == 1:
            data['data'] = data['data'][0]
        return data

    def brief_str(self):
        return self.__str__()

    def get_full_string(self):
        if isinstance(self.data, pd.DataFrame):
            return self.data.to_string()
        else:
            return str(self.data)

    def __str__(self):
        base_string = f"Data name: {self.name}\nDescription: {self.description}\nSource: {self.source}\n"
        base_string += f"Data type: {type(self.data)}\n"
        if isinstance(self.data, pd.DataFrame):
            format_string = ""
            format_string += f"First five rows:\n{self.data.head().to_string()}\n"
        elif isinstance(self.data, dict):
            format_string = "Partial data preview: "
            format_string += str(self.data)[:100]
        elif isinstance(self.data, list):
            format_string = "Partial data preview: "
            format_string += str(self.data)[:100]
        else:
            format_string = "Partial data preview: "
            format_string += str(self.data)[:100]

        return base_string + format_string

    def __repr__(self):
        return self.__str__()
    
    def __hash__(self):
        return hash(self.name+self.description)
    
    def __eq__(self, other):
        if not isinstance(other, ToolResult):
            return False
        return self.name == other.name and self.description == other.description
