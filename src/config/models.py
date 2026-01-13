"""
Pydantic 配置模型
提供类型安全的配置验证和自动补全
"""
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator, model_validator
import os


class LLMGenerationParams(BaseModel):
    """LLM 生成参数配置"""
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="生成温度")
    max_tokens: int = Field(default=32768, gt=0, description="最大生成 token 数")
    top_p: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="核采样参数")
    frequency_penalty: Optional[float] = Field(default=None, ge=-2.0, le=2.0, description="频率惩罚")
    presence_penalty: Optional[float] = Field(default=None, ge=-2.0, le=2.0, description="存在惩罚")

    class Config:
        extra = "allow"  # 允许额外字段


class LLMConfig(BaseModel):
    """单个 LLM 配置"""
    model_name: str = Field(..., description="模型名称")
    api_key: str = Field(..., description="API 密钥")
    base_url: str = Field(..., description="API 基础 URL")
    generation_params: LLMGenerationParams = Field(
        default_factory=LLMGenerationParams,
        description="生成参数"
    )

    @field_validator('base_url')
    @classmethod
    def validate_base_url(cls, v: str) -> str:
        """验证 base_url 格式"""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('base_url 必须以 http:// 或 https:// 开头')
        return v.rstrip('/')


class TargetConfig(BaseModel):
    """目标配置"""
    target_name: str = Field(..., description="目标名称")
    stock_code: Optional[str] = Field(default=None, description="股票代码")
    target_type: Literal['financial_company', 'macro', 'industry', 'general'] = Field(
        default='financial_company',
        description="目标类型"
    )
    language: Literal['zh', 'en'] = Field(default='zh', description="报告语言")


class PathConfig(BaseModel):
    """路径配置"""
    output_dir: str = Field(default='./outputs', description="输出目录")
    reference_doc_path: Optional[str] = Field(default=None, description="参考文档路径")
    outline_template_path: Optional[str] = Field(default=None, description="大纲模板路径")

    @field_validator('reference_doc_path', 'outline_template_path')
    @classmethod
    def validate_file_exists(cls, v: Optional[str]) -> Optional[str]:
        """验证文件是否存在"""
        if v is not None and not os.path.exists(v):
            raise ValueError(f'文件不存在: {v}')
        return v


class CacheConfig(BaseModel):
    """缓存配置"""
    use_collect_data_cache: bool = Field(default=True, description="使用数据收集缓存")
    use_analysis_cache: bool = Field(default=True, description="使用分析缓存")
    use_report_outline_cache: bool = Field(default=True, description="使用报告大纲缓存")
    use_full_report_cache: bool = Field(default=True, description="使用完整报告缓存")
    use_post_process_cache: bool = Field(default=True, description="使用后处理缓存")


class TaskConfig(BaseModel):
    """任务配置"""
    custom_collect_tasks: List[str] = Field(default_factory=list, description="自定义收集任务")
    custom_analysis_tasks: List[str] = Field(default_factory=list, description="自定义分析任务")
    max_collect_tasks: int = Field(default=5, ge=1, le=20, description="最大收集任务数")
    max_analysis_tasks: int = Field(default=5, ge=1, le=20, description="最大分析任务数")


class AppConfig(BaseModel):
    """应用主配置"""
    # 目标配置
    target_name: str = Field(..., description="目标名称")
    stock_code: Optional[str] = Field(default=None, description="股票代码")
    target_type: Literal['financial_company', 'macro', 'industry', 'general'] = Field(
        default='financial_company',
        description="目标类型"
    )
    language: Literal['zh', 'en'] = Field(default='zh', description="报告语言")

    # 路径配置
    output_dir: str = Field(default='./outputs', description="输出目录")
    reference_doc_path: Optional[str] = Field(default=None, description="参考文档路径")
    outline_template_path: Optional[str] = Field(default=None, description="大纲模板路径")

    # LLM 配置
    llm_config_list: List[LLMConfig] = Field(..., description="LLM 配置列表")

    # 缓存配置
    use_collect_data_cache: bool = Field(default=True, description="使用数据收集缓存")
    use_analysis_cache: bool = Field(default=True, description="使用分析缓存")
    use_report_outline_cache: bool = Field(default=True, description="使用报告大纲缓存")
    use_full_report_cache: bool = Field(default=True, description="使用完整报告缓存")
    use_post_process_cache: bool = Field(default=True, description="使用后处理缓存")

    # 任务配置
    custom_collect_tasks: List[str] = Field(default_factory=list, description="自定义收集任务")
    custom_analysis_tasks: List[str] = Field(default_factory=list, description="自定义分析任务")

    # 其他配置
    save_note: Optional[str] = Field(default=None, description="保存备注")
    working_dir: Optional[str] = Field(default=None, description="工作目录（自动生成）")

    class Config:
        extra = "allow"  # 允许额外字段以保持向后兼容

    @model_validator(mode='after')
    def validate_config(self):
        """模型级别的验证"""
        # 验证至少有一个 LLM 配置
        if not self.llm_config_list:
            raise ValueError('至少需要配置一个 LLM')

        return self
