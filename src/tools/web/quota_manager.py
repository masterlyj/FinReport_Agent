"""
搜索引擎配额管理器

负责追踪和管理各搜索引擎的API配额使用情况
支持月度自动重置和持久化存储
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from ...utils.logger import get_logger

logger = get_logger()


class QuotaManager:
    """搜索引擎配额管理器"""
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        初始化配额管理器
        
        Args:
            storage_path: 配额数据存储路径，默认为项目根目录下的 .search_quotas.json
        """
        if storage_path is None:
            # 使用当前工作目录（通常是项目根目录）
            project_root = Path(os.getcwd())
            storage_path = project_root / ".search_quotas.json"
        
        self.storage_path = Path(storage_path)
        
        # 配额限制配置（每月）
        self.quota_limits = {
            "serpapi": 250,      # 250次/月
            "tavily": 1000,      # 1000次/月
            "duckduckgo": -1,    # 无限
            "serper": 2500,      # 2500次
            "bing": 1000,        # 根据Azure配置
        }
        
        self.quotas = self._load_quotas()
        logger.info(f"QuotaManager initialized with storage: {self.storage_path}")
    
    def _load_quotas(self) -> Dict:
        """从文件加载配额使用情况"""
        if not self.storage_path.exists():
            logger.info("Quota file not found, initializing new quotas")
            return self._init_quotas()
        
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 检查是否需要重置（每月1号）
            last_reset = datetime.fromisoformat(data.get("last_reset", "2000-01-01T00:00:00"))
            current = datetime.now()
            
            # 如果月份不同，重置配额
            if current.year != last_reset.year or current.month != last_reset.month:
                logger.info(f"Monthly reset triggered (last reset: {last_reset.date()}, current: {current.date()})")
                return self._init_quotas()
            
            logger.info(f"Loaded quotas from {self.storage_path}")
            return data
            
        except Exception as e:
            logger.error(f"Failed to load quotas: {e}, initializing new quotas")
            return self._init_quotas()
    
    def _init_quotas(self) -> Dict:
        """初始化配额数据"""
        data = {
            "last_reset": datetime.now().isoformat(),
            "quotas": {}
        }
        
        # 为每个引擎初始化配额
        for engine, limit in self.quota_limits.items():
            data["quotas"][engine] = {
                "used": 0,
                "limit": limit
            }
        
        self._save_quotas(data)
        logger.info(f"Initialized fresh quotas for {len(self.quota_limits)} engines")
        return data
    
    def _save_quotas(self, data: Dict):
        """保存配额数据到文件"""
        try:
            # 确保父目录存在
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Saved quotas to {self.storage_path}")
        except Exception as e:
            logger.error(f"Failed to save quotas: {e}")
    
    def check_quota(self, engine_name: str) -> bool:
        """
        检查引擎是否还有配额
        
        Args:
            engine_name: 引擎名称 (serpapi, tavily, duckduckgo等)
        
        Returns:
            True if有配额可用，False if配额已用尽
        """
        if engine_name not in self.quotas.get("quotas", {}):
            logger.warning(f"Engine '{engine_name}' not found in quota config")
            return False
        
        quota_info = self.quotas["quotas"][engine_name]
        limit = quota_info["limit"]
        
        if limit == -1:  # 无限配额
            return True
        
        used = quota_info["used"]
        has_quota = used < limit
        
        if not has_quota:
            logger.warning(f"Engine '{engine_name}' quota exhausted: {used}/{limit}")
        
        return has_quota
    
    def use_quota(self, engine_name: str, count: int = 1):
        """
        记录配额使用
        
        Args:
            engine_name: 引擎名称
            count: 使用次数（默认1次）
        """
        if engine_name not in self.quotas.get("quotas", {}):
            logger.warning(f"Cannot record quota for unknown engine: {engine_name}")
            return
        
        self.quotas["quotas"][engine_name]["used"] += count
        self._save_quotas(self.quotas)
        
        remaining = self.get_remaining(engine_name)
        logger.info(f"Used quota for '{engine_name}': +{count}, remaining: {remaining}")
    
    def get_remaining(self, engine_name: str) -> int:
        """
        获取剩余配额数量
        
        Args:
            engine_name: 引擎名称
        
        Returns:
            剩余配额数，-1表示无限
        """
        if engine_name not in self.quotas.get("quotas", {}):
            return 0
        
        quota_info = self.quotas["quotas"][engine_name]
        limit = quota_info["limit"]
        
        if limit == -1:
            return -1  # 无限
        
        used = quota_info["used"]
        return max(0, limit - used)
    
    def get_status(self) -> Dict:
        """
        获取所有引擎的配额状态
        
        Returns:
            Dict: 每个引擎的配额使用情况
                {
                    "serpapi": {
                        "used": 45,
                        "limit": 250,
                        "remaining": 205,
                        "percentage": 82.0
                    },
                    ...
                }
        """
        status = {}
        
        for engine, info in self.quotas.get("quotas", {}).items():
            limit = info["limit"]
            used = info["used"]
            
            if limit == -1:
                remaining = "Unlimited"
                percentage = 100.0
            else:
                remaining = max(0, limit - used)
                percentage = (remaining / limit * 100) if limit > 0 else 0
            
            status[engine] = {
                "used": used,
                "limit": limit if limit != -1 else "Unlimited",
                "remaining": remaining,
                "percentage": round(percentage, 1)
            }
        
        return status
    
    def reset_quota(self, engine_name: Optional[str] = None):
        """
        手动重置配额（用于测试或月度重置）
        
        Args:
            engine_name: 指定引擎名称，None则重置所有
        """
        if engine_name:
            if engine_name in self.quotas.get("quotas", {}):
                self.quotas["quotas"][engine_name]["used"] = 0
                logger.info(f"Reset quota for '{engine_name}'")
            else:
                logger.warning(f"Cannot reset unknown engine: {engine_name}")
        else:
            # 重置所有
            for engine in self.quotas.get("quotas", {}).keys():
                self.quotas["quotas"][engine]["used"] = 0
            self.quotas["last_reset"] = datetime.now().isoformat()
            logger.info("Reset all quotas")
        
        self._save_quotas(self.quotas)
    
    def __str__(self) -> str:
        """返回配额状态的可读字符串"""
        lines = ["Search Engine Quota Status:"]
        status = self.get_status()
        
        for engine, info in status.items():
            if info["limit"] == "Unlimited":
                lines.append(f"  {engine:15} | Used: {info['used']:4} | Unlimited")
            else:
                lines.append(
                    f"  {engine:15} | {info['used']:4}/{info['limit']:4} "
                    f"({info['percentage']:5.1f}% remaining)"
                )
        
        return "\n".join(lines)


# 便捷函数：命令行工具
def print_quota_status():
    """打印配额状态（命令行工具）"""
    manager = QuotaManager()
    print(manager)
    

if __name__ == "__main__":
    # 测试代码
    print("=== Quota Manager Test ===\n")
    
    manager = QuotaManager()
    
    # 打印初始状态
    print(manager)
    print()
    
    # 模拟使用配额
    print("Using quotas...")
    manager.use_quota("serpapi", 5)
    manager.use_quota("duckduckgo", 10)
    
    print()
    print(manager)
