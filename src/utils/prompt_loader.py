"""基于 YAML 的提示词模板加载器。"""

import os
import yaml
import warnings
from typing import Dict, Any, Optional
from pathlib import Path


class PromptLoader:
    """加载并管理来自 YAML 配置文件的提示词。"""
    
    def __init__(self, prompts_dir: str, report_type: str = "general"):
        """
        初始化加载器。
        
        Args:
            prompts_dir: 提示词文件所在的目录路径。
            report_type: 报告类型（如 'financial_company', 'macro'），用于查找特定的 YAML 文件。
        """
        self.prompts_dir = Path(prompts_dir)
        self.report_type = report_type
        self.prompts: Dict[str, Any] = {}
        
        if not self.prompts_dir.exists():
            raise ValueError(f"未找到提示词目录: {self.prompts_dir}")
        
        self._load_prompts()
    
    def _load_prompts(self):
        """
        根据 report_type 从 YAML 文件加载提示词。
        
        采用回退机制（Fallback Mechanism）：
        1. 优先尝试精确匹配报告类型的全名（如 financial_company_prompts.yaml）。
        2. 其次尝试匹配报告类型的前缀（如 financial_prompts.yaml）。
        3. 最后回退到默认的 prompts.yaml。
        """
        # 构造可能的文件路径
        specific_file = self.prompts_dir / f"{self.report_type}_prompts.yaml"
        parent_specific_file = self.prompts_dir / f"{self.report_type.split('_')[0]}_prompts.yaml"
        default_file = self.prompts_dir / "prompts.yaml"
        
        # 按照优先级查找存在的文件
        yaml_file = None
        if specific_file.exists():
            yaml_file = specific_file
        elif parent_specific_file.exists():
            yaml_file = parent_specific_file
        elif default_file.exists():
            yaml_file = default_file
        else:
            raise FileNotFoundError(
                f"在 {self.prompts_dir} 中未找到提示词文件。 "
                f"预期文件: '{specific_file.name}' 或 '{default_file.name}'"
            )
        
        # 加载 YAML 内容
        with open(yaml_file, 'r', encoding='utf-8') as f:
            self.prompts = yaml.safe_load(f) or {}
    
    def get_prompt(self, prompt_key: str, **kwargs) -> str:
        """
        获取提示词模板，并可选地使用 kwargs 进行格式化。
        
        Args:
            prompt_key: YAML 中的键名。
            **kwargs: 用于 Python str.format() 的变量。
            
        Returns:
            格式化后的提示词字符串；如果键不存在则返回 None 并触发警告。
        """
        if prompt_key not in self.prompts:
            warnings.warn(f"在 {self.prompts_dir} 中未找到提示词 '{prompt_key}'。 "
                f"可用键: {list(self.prompts.keys())}"
            )
            return None
            
        prompt_template = self.prompts[prompt_key]
        
        # 如果提供了参数，则执行格式化
        if kwargs:
            try:
                return prompt_template.format(**kwargs)
            except KeyError as e:
                # Fail Fast: 如果缺少必要的格式化变量，立即抛出错误
                raise KeyError(
                    f"提示词 '{prompt_key}' 缺少必要的格式化参数 {e}"
                )
        
        return prompt_template
    
    def get_all_prompts(self) -> Dict[str, str]:
        """获取所有已加载的提示词。"""
        return self.prompts.copy()
    
    def list_available_prompts(self) -> list:
        """列出所有可用的提示词键名。"""
        return list(self.prompts.keys())
    
    def reload(self, report_type: Optional[str] = None):
        """重新加载提示词，可选地更改报告类型。"""
        if report_type:
            self.report_type = report_type
        self.prompts = {}
        self._load_prompts()
    
    @staticmethod
    def create_loader_for_agent(agent_name: str, report_type: str = "general") -> 'PromptLoader':
        """
        为特定智能体创建 PromptLoader 实例。
        
        路径约定: src/agents/{agent_name}/prompts/
        """
        current_file = Path(__file__)
        src_dir = current_file.parent.parent
        prompts_dir = src_dir / "agents" / agent_name / "prompts"
        
        return PromptLoader(str(prompts_dir), report_type=report_type)
    
    @staticmethod
    def create_loader_for_memory(report_type: str = "general") -> 'PromptLoader':
        """
        为 Memory 模块创建 PromptLoader 实例。
        
        路径约定: src/memory/prompts/
        """
        current_file = Path(__file__)
        src_dir = current_file.parent.parent
        prompts_dir = src_dir / "memory" / "prompts"
        
        return PromptLoader(str(prompts_dir), report_type=report_type)


def get_prompt_loader(module_name: str, report_type: str = "general") -> PromptLoader:
    """
    通用工厂函数，根据模块名获取对应的 PromptLoader。
    
    Args:
        module_name: 模块名称（如 'data_collector', 'memory'）。
        report_type: 报告类型。
    """
    if module_name == "memory":
        return PromptLoader.create_loader_for_memory(report_type)
    else:
        return PromptLoader.create_loader_for_agent(module_name, report_type)
